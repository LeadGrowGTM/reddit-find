"""Reddit JSON API fetching — posts and comments, no auth required."""

import time
from typing import Dict, List, Optional

import requests

HEADERS = {
    "User-Agent": "reddit-find/1.0 GTM research tool (github.com/LeadGrowGTM/reddit-find)"
}
BASE_URL = "https://old.reddit.com"


def fetch_subreddit_posts(
    subreddit: str,
    sort: str = "hot",
    limit: int = 25,
    time_filter: str = "month",
) -> List[Dict]:
    """Fetch posts from a subreddit. sort: hot | new | top | rising"""
    url = f"{BASE_URL}/r/{subreddit}/{sort}.json"
    params: Dict = {"limit": limit}
    if sort == "top":
        params["t"] = time_filter

    data = _get(url, params)
    if not data:
        return []

    posts = []
    for child in data.get("data", {}).get("children", []):
        p = child.get("data", {})
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
                "created_utc": p.get("created_utc", 0),
                "flair": p.get("link_flair_text") or "",
            }
        )

    return sorted(posts, key=lambda x: x["score"], reverse=True)


def fetch_post_comments(subreddit: str, post_id: str, limit: int = 25) -> List[Dict]:
    """Fetch top comments from a post."""
    url = f"{BASE_URL}/r/{subreddit}/comments/{post_id}.json"
    time.sleep(2)

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


def _get(url: str, params: Dict, array_response: bool = False, retry: bool = True):
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if resp.status_code == 429:
            if retry:
                time.sleep(15)
                return _get(url, params, array_response, retry=False)
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None
