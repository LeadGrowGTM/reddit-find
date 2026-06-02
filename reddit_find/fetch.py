"""Reddit JSON API fetching — posts and comments, no auth required."""

import random
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

from .errors import RedditBlockedError, RedditRateLimitError
from .ratelimit import get_limiter

HEADERS = {
    "User-Agent": "reddit-find/1.0 GTM research tool (github.com/LeadGrowGTM/reddit-find)"
}
BASE_URL = "https://old.reddit.com"

# Markers seen on Reddit's WAF block page. Matched case-insensitively against
# the response body. Kept apostrophe-free so HTML entity encoding can't dodge it.
_BLOCK_MARKERS = ("blocked by network security", "<title>blocked</title>")


def _raise_if_blocked(resp) -> None:
    """Raise RedditBlockedError if the response is a 403 or a WAF block page."""
    blocked = resp.status_code == 403
    if not blocked:
        body = (resp.text or "").lower()
        blocked = any(marker in body for marker in _BLOCK_MARKERS)
    if blocked:
        raise RedditBlockedError(
            "Reddit has blocked this IP (rate-limit/WAF). Wait it out, switch "
            "networks/VPN, or use the RapidAPI fallback (separate feature)."
        )


def fetch_subreddit_posts(
    subreddit: str,
    sort: str = "hot",
    limit: int = 25,
    time_filter: str = "month",
    max_age_days: Optional[int] = None,
) -> List[Dict]:
    """Fetch posts from a subreddit. sort: hot | new | top | rising

    max_age_days: if set, filter out posts older than N days (uses created_utc).
    """
    url = f"{BASE_URL}/r/{subreddit}/{sort}.json"
    params: Dict = {"limit": limit}
    if sort == "top":
        params["t"] = time_filter

    data = _get(url, params)
    if not data:
        return []

    now_ts = datetime.now(timezone.utc).timestamp()
    cutoff_ts = (now_ts - max_age_days * 86400) if max_age_days is not None else None

    posts = []
    for child in data.get("data", {}).get("children", []):
        p = child.get("data", {})
        created_utc = p.get("created_utc", 0)

        # Apply recency filter
        if cutoff_ts is not None and created_utc < cutoff_ts:
            continue

        posts.append(
            {
                "id": p.get("id", ""),
                "title": p.get("title", ""),
                "score": p.get("score", 0),
                "upvote_ratio": p.get("upvote_ratio", 0),
                "num_comments": p.get("num_comments", 0),
                "author": p.get("author", "[deleted]"),
                "url": f"https://reddit.com{p.get('permalink', '')}",
                "selftext": (p.get("selftext") or "")[:600],
                "subreddit": p.get("subreddit", subreddit),
                "created_utc": created_utc,
                "flair": p.get("link_flair_text") or "",
            }
        )

    return sorted(posts, key=lambda x: x["score"], reverse=True)


def fetch_post_comments(subreddit: str, post_id: str, limit: int = 25) -> List[Dict]:
    """Fetch top comments from a post."""
    url = f"{BASE_URL}/r/{subreddit}/comments/{post_id}.json"
    raw = _get(url, {"limit": limit, "sort": "top"}, array_response=True)
    if not raw or len(raw) < 2:
        return []

    comments = []
    for child in raw[1].get("data", {}).get("children", []):
        if child.get("kind") != "t1":
            continue
        c = child.get("data", {})
        body = (c.get("body") or "").strip()
        if not body or body == "[deleted]" or body == "[removed]":
            continue
        comments.append(
            {
                "author": c.get("author", "[deleted]"),
                "score": c.get("score", 0),
                "body": body[:800],
            }
        )

    return sorted(comments, key=lambda x: x["score"], reverse=True)[:12]


def fetch_single_post(post_url_or_id: str, subreddit: Optional[str] = None) -> Optional[Dict]:
    """Fetch a single post + all its comments (up to 50).

    Accepts a full Reddit URL (https://reddit.com/r/sub/comments/id/...) or
    a bare post ID (e.g. "1abc23"). Returns a dict with post metadata + comments.
    """
    # Parse URL to extract subreddit + post_id if full URL provided
    sub, post_id = _parse_post_ref(post_url_or_id, subreddit)
    if not post_id:
        return None

    if sub:
        url = f"{BASE_URL}/r/{sub}/comments/{post_id}.json"
    else:
        # Try without subreddit path (Reddit redirects)
        url = f"{BASE_URL}/comments/{post_id}.json"

    raw = _get(url, {"limit": 50, "sort": "top"}, array_response=True)
    if not raw or len(raw) < 2:
        return None

    # Post data is first element
    post_children = raw[0].get("data", {}).get("children", [])
    if not post_children:
        return None

    p = post_children[0].get("data", {})
    created_utc = p.get("created_utc", 0)
    post_date = datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d") if created_utc else "unknown"

    post = {
        "id": p.get("id", post_id),
        "title": p.get("title", ""),
        "score": p.get("score", 0),
        "upvote_ratio": p.get("upvote_ratio", 0),
        "num_comments": p.get("num_comments", 0),
        "author": p.get("author", "[deleted]"),
        "url": f"https://reddit.com{p.get('permalink', '')}",
        "selftext": (p.get("selftext") or "").strip(),
        "subreddit": p.get("subreddit", sub or ""),
        "created_utc": created_utc,
        "post_date": post_date,
        "flair": p.get("link_flair_text") or "",
    }

    # Comments — collect up to 50
    comments = []
    for child in raw[1].get("data", {}).get("children", []):
        if child.get("kind") != "t1":
            continue
        c = child.get("data", {})
        body = (c.get("body") or "").strip()
        if not body or body == "[deleted]" or body == "[removed]":
            continue
        comments.append(
            {
                "author": c.get("author", "[deleted]"),
                "score": c.get("score", 0),
                "body": body[:1200],
            }
        )

    post["comments"] = sorted(comments, key=lambda x: x["score"], reverse=True)[:50]
    return post


def search_posts(
    query: str,
    subreddits: Optional[List[str]] = None,
    max_age_days: Optional[int] = 365,
    min_score: int = 5,
    limit: int = 25,
    sort: str = "relevance",
) -> List[Dict]:
    """Search Reddit for posts matching a keyword query.

    Uses Reddit's search.json endpoint — finds posts by keyword anywhere in
    title/body, not just hot/top posts. Scoped to subreddits if provided,
    otherwise global search.

    sort: relevance | top | new | comments
    """
    now_ts = datetime.now(timezone.utc).timestamp()
    cutoff_ts = (now_ts - max_age_days * 86400) if max_age_days is not None else None

    all_posts: List[Dict] = []

    if subreddits:
        for sub in subreddits:
            url = f"{BASE_URL}/r/{sub}/search.json"
            params = {
                "q": query,
                "restrict_sr": "on",
                "sort": sort,
                "t": "all",
                "limit": limit,
            }
            data = _get(url, params)
            if not data:
                continue
            all_posts.extend(_parse_search_results(data, cutoff_ts, min_score))
    else:
        url = f"{BASE_URL}/search.json"
        params = {
            "q": query,
            "type": "link",
            "sort": sort,
            "t": "all",
            "limit": limit,
        }
        data = _get(url, params)
        if data:
            all_posts.extend(_parse_search_results(data, cutoff_ts, min_score))

    # Deduplicate by post ID
    seen: set = set()
    deduped = []
    for p in all_posts:
        if p["id"] not in seen:
            seen.add(p["id"])
            deduped.append(p)

    return sorted(deduped, key=lambda x: x["score"], reverse=True)


def _parse_search_results(data: Dict, cutoff_ts: Optional[float], min_score: int) -> List[Dict]:
    posts = []
    for child in data.get("data", {}).get("children", []):
        p = child.get("data", {})
        created_utc = p.get("created_utc", 0)
        score = p.get("score", 0)

        if cutoff_ts is not None and created_utc < cutoff_ts:
            continue
        if score < min_score:
            continue

        posts.append(
            {
                "id": p.get("id", ""),
                "title": p.get("title", ""),
                "score": score,
                "upvote_ratio": p.get("upvote_ratio", 0),
                "num_comments": p.get("num_comments", 0),
                "author": p.get("author", "[deleted]"),
                "url": f"https://reddit.com{p.get('permalink', '')}",
                "selftext": (p.get("selftext") or "")[:600],
                "subreddit": p.get("subreddit", ""),
                "created_utc": created_utc,
                "flair": p.get("link_flair_text") or "",
            }
        )
    return posts


def _parse_post_ref(ref: str, subreddit: Optional[str] = None):
    """Extract (subreddit, post_id) from a URL or bare ID."""
    # Full URL: https://reddit.com/r/sales/comments/abc123/title_here/
    match = re.search(r"/r/([^/]+)/comments/([a-z0-9]+)", ref, re.IGNORECASE)
    if match:
        return match.group(1), match.group(2)

    # Bare ID (alphanumeric, 5-7 chars typical)
    if re.match(r"^[a-z0-9]{4,10}$", ref, re.IGNORECASE):
        return subreddit, ref

    return subreddit, None


_BACKOFF_SCHEDULE = (5, 15, 45)  # seconds before each successive 429 retry


def _jittered(seconds: float) -> float:
    """Apply ±20% random jitter so retries don't hit Reddit metronomically."""
    return seconds * random.uniform(0.8, 1.2)


def _get(url: str, params: Dict, array_response: bool = False, max_retries: int = 3):
    attempt = 0
    try:
        while True:
            get_limiter().acquire()
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
            _raise_if_blocked(resp)
            if resp.status_code == 429:
                if attempt >= max_retries:
                    raise RedditRateLimitError(
                        f"Reddit rate-limited this IP (HTTP 429) after {max_retries} "
                        "backoff retries. Slow down (--max-per-minute) or wait before retrying."
                    )
                base = _BACKOFF_SCHEDULE[min(attempt, len(_BACKOFF_SCHEDULE) - 1)]
                time.sleep(_jittered(base))
                attempt += 1
                continue
            resp.raise_for_status()
            return resp.json()
    except (RedditBlockedError, RedditRateLimitError):
        raise
    except Exception:
        return None
