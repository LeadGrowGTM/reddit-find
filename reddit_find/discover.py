"""Subreddit discovery via SerperDev Google Search."""

import re
import requests
from typing import Dict, List


SERPER_URL = "https://google.serper.dev/search"

BLOCKED_SUBS = {
    "all", "popular", "new", "best", "rising", "controversial",
    "random", "randnsfw", "friends", "modnews", "longtail",
}


def find_subreddits(topic: str, serper_api_key: str, num_results: int = 8) -> List[Dict]:
    """
    Use SerperDev to find the most relevant subreddits for a GTM topic.
    Returns subreddits ranked by how often they appear across discovery queries.
    """
    queries = [
        f'site:reddit.com "{topic}"',
        f'reddit "{topic}" community discussion problems',
        f'best subreddit for "{topic}" B2B',
        f'r/ "{topic}" pain frustration complain site:reddit.com',
    ]

    scores: Dict[str, int] = {}

    for query in queries:
        results = _serper_search(query, serper_api_key)
        for result in results:
            text = result.get("link", "") + " " + result.get("snippet", "") + " " + result.get("title", "")
            for sub in _extract_subreddits(text):
                scores[sub] = scores.get(sub, 0) + 1

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [{"subreddit": sub, "relevance_score": score} for sub, score in ranked[:num_results]]


def _serper_search(query: str, api_key: str) -> List[Dict]:
    resp = requests.post(
        SERPER_URL,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": 10},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("organic", [])


def _extract_subreddits(text: str) -> List[str]:
    found = set()
    for pattern in [r"reddit\.com/r/([a-zA-Z0-9_]+)", r"\br/([a-zA-Z0-9_]+)\b"]:
        for match in re.findall(pattern, text):
            clean = match.rstrip("/")
            if len(clean) > 2 and clean.lower() not in BLOCKED_SUBS:
                found.add(clean)
    return list(found)
