"""Subreddit discovery via Reddit native search (no key required) + optional SerperDev."""

import os
import re
import requests
from typing import Dict, List, Optional


SERPER_URL = "https://google.serper.dev/search"
REDDIT_SEARCH_URL = "https://old.reddit.com/search.json"

HEADERS = {
    "User-Agent": "reddit-find/1.0 GTM research tool (github.com/LeadGrowGTM/reddit-find)"
}

BLOCKED_SUBS = {
    "all", "popular", "new", "best", "rising", "controversial",
    "random", "randnsfw", "friends", "modnews", "longtail",
}


def find_subreddits(topic: str, serper_api_key: Optional[str] = None, num_results: int = 8) -> List[Dict]:
    """
    Find relevant subreddits for a GTM topic.

    Primary: Reddit native subreddit search (no key required).
    Optional: If serper_api_key provided, also runs SerperDev searches and merges results.

    Returns ranked list with subreddit, subscribers, description.
    """
    scores: Dict[str, int] = {}
    sub_meta: Dict[str, Dict] = {}

    # --- Primary: Reddit native subreddit search ---
    reddit_results = _reddit_subreddit_search(topic, limit=15)
    for r in reddit_results:
        sub = r["subreddit"]
        scores[sub] = scores.get(sub, 0) + 2  # weight native results higher
        sub_meta[sub] = r

    # --- Optional: SerperDev (additive) ---
    if serper_api_key:
        queries = [
            f'site:reddit.com "{topic}"',
            f'reddit "{topic}" community discussion problems',
            f'best subreddit for "{topic}" B2B',
            f'r/ "{topic}" pain frustration complain site:reddit.com',
        ]
        for query in queries:
            results = _serper_search(query, serper_api_key)
            for result in results:
                text = result.get("link", "") + " " + result.get("snippet", "") + " " + result.get("title", "")
                for sub in _extract_subreddits(text):
                    scores[sub] = scores.get(sub, 0) + 1

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    output = []
    for sub, score in ranked[:num_results]:
        meta = sub_meta.get(sub, {})
        output.append({
            "subreddit": sub,
            "relevance_score": score,
            "subscribers": meta.get("subscribers", 0),
            "description": meta.get("description", ""),
        })

    return output


def _reddit_subreddit_search(topic: str, limit: int = 15) -> List[Dict]:
    """Search Reddit's own subreddit search API. No API key required."""
    try:
        resp = requests.get(
            REDDIT_SEARCH_URL,
            headers=HEADERS,
            params={"q": topic, "type": "sr", "limit": limit},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    results = []
    for child in data.get("data", {}).get("children", []):
        sr = child.get("data", {})
        name = sr.get("display_name", "")
        if not name or name.lower() in BLOCKED_SUBS:
            continue
        results.append({
            "subreddit": name,
            "subscribers": sr.get("subscribers", 0),
            "description": (sr.get("public_description") or sr.get("description") or "")[:200],
        })

    # sort by subscribers descending so biggest communities bubble up
    return sorted(results, key=lambda x: x["subscribers"], reverse=True)


def _serper_search(query: str, api_key: str) -> List[Dict]:
    try:
        resp = requests.post(
            SERPER_URL,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": 10},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("organic", [])
    except Exception:
        return []


def _extract_subreddits(text: str) -> List[str]:
    found = set()
    for pattern in [r"reddit\.com/r/([a-zA-Z0-9_]+)", r"\br/([a-zA-Z0-9_]+)\b"]:
        for match in re.findall(pattern, text):
            clean = match.rstrip("/")
            if len(clean) > 2 and clean.lower() not in BLOCKED_SUBS:
                found.add(clean)
    return list(found)
