"""reddit-find CLI - pure data fetcher for Reddit GTM research."""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click
from dotenv import load_dotenv

# Load SERPER_API_KEY from workspace .env if present (optional)
load_dotenv(Path(__file__).parents[2] / ".env", override=False)
load_dotenv(Path("C:/Users/mitch/Everything_CC/.env"), override=False)

from . import __version__
from .discover import find_subreddits
from .fetch import fetch_post_comments, fetch_subreddit_posts


@click.group()
@click.version_option(version=__version__)
def cli():
    """reddit-find - fetch Reddit data for GTM research.

    Discovers relevant subreddits and fetches top threads + comments as
    structured markdown. No API key required. Claude in session handles analysis.
    """
    pass


@cli.command()
@click.argument("topic")
@click.option("--serper-key", envvar="SERPER_API_KEY", default=None, help="SerperDev API key (optional, improves discovery)")
@click.option("--top", default=8, show_default=True, help="Number of subreddits to return")
def discover(topic: str, serper_key: Optional[str], top: int):
    """Find relevant subreddits for a GTM topic.

    TOPIC: The topic or ICP problem to research (e.g. "b2b cold email")

    Uses Reddit's native subreddit search by default. Pass SERPER_API_KEY
    for enhanced discovery via Google.
    """
    click.echo(f"Searching for subreddits: {topic}\n")
    subreddits = find_subreddits(topic, serper_api_key=serper_key, num_results=top)

    if not subreddits:
        click.echo("No subreddits found. Try a broader topic.", err=True)
        sys.exit(1)

    click.echo(f"Top subreddits for '{topic}':\n")
    for i, s in enumerate(subreddits, 1):
        subs_str = f"{s['subscribers']:,}" if s["subscribers"] else "?"
        desc = s.get("description", "")[:60]
        click.echo(f"  {i:2}. r/{s['subreddit']:<30} {subs_str:>10} subscribers  {desc}")

    click.echo(f"\nRun the full pipeline:")
    subs_flags = " ".join(f"-s {s['subreddit']}" for s in subreddits[:5])
    click.echo(f"  reddit-find fetch \"{topic}\" {subs_flags}")


@cli.command()
@click.argument("topic")
@click.option("--serper-key", envvar="SERPER_API_KEY", default=None, help="SerperDev API key (optional, improves subreddit discovery)")
@click.option("--subreddit", "-s", multiple=True, help="Target specific subreddits (skips discovery)")
@click.option("--posts-per-sub", default=20, show_default=True, help="Posts to fetch per subreddit")
@click.option("--min-score", default=5, show_default=True, help="Minimum post score to include")
@click.option("--top-threads", default=8, show_default=True, help="Top threads to fetch per subreddit")
@click.option("--output", "-o", default=None, help="Save output to file (default: stdout)")
def fetch(
    topic: str,
    serper_key: Optional[str],
    subreddit: tuple,
    posts_per_sub: int,
    min_score: int,
    top_threads: int,
    output: Optional[str],
):
    """Fetch Reddit threads and output structured markdown for analysis.

    TOPIC: What you're researching (e.g. "b2b pipeline generation")

    No API key required. Output is structured markdown — Claude reads it
    and extracts pain points, buyer language, viral moments, and content angles.

    \b
    Examples:
      reddit-find fetch "b2b cold email" -s sales --min-score 20 -o research.md
      reddit-find fetch "SaaS churn" -s CustomerSuccess -s churnzero -o churn.md
    """
    # Step 1: Determine subreddits
    if subreddit:
        target_subs = list(subreddit)
        click.echo(f"Targeting: {', '.join(f'r/{s}' for s in target_subs)}\n", err=True)
    else:
        method = "Reddit native search"
        if serper_key:
            method = "Reddit native search + SerperDev"
        click.echo(f"Discovering subreddits for: {topic} ({method})...", err=True)
        discovered = find_subreddits(topic, serper_api_key=serper_key)
        if not discovered:
            click.echo("No subreddits found. Try passing -s <subreddit> directly.", err=True)
            sys.exit(1)
        target_subs = [s["subreddit"] for s in discovered[:5]]
        click.echo(f"Targeting: {', '.join(f'r/{s}' for s in target_subs)}\n", err=True)

    # Step 2: Fetch posts + comments
    all_threads = []
    for sub in target_subs:
        click.echo(f"Fetching r/{sub}...", err=True)

        hot = fetch_subreddit_posts(sub, sort="hot", limit=posts_per_sub)
        top = fetch_subreddit_posts(sub, sort="top", limit=posts_per_sub, time_filter="month")
        posts = _dedupe(hot + top)
        posts = [p for p in posts if p["score"] >= min_score]
        posts = sorted(posts, key=lambda x: x["score"], reverse=True)[:top_threads]

        click.echo(f"  {len(posts)} threads (fetching comments...)", err=True)
        for post in posts:
            post["comments"] = fetch_post_comments(sub, post["id"]) or []

        all_threads.extend(posts)

    if not all_threads:
        click.echo("No threads fetched. Check subreddit names or lower --min-score.", err=True)
        sys.exit(1)

    click.echo(f"\nFetched {len(all_threads)} threads. Building markdown...\n", err=True)

    # Step 3: Build structured markdown (no analysis — Claude handles that)
    report = _build_markdown(topic, target_subs, all_threads)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(report)
        click.echo(f"Saved to: {output}", err=True)
    else:
        click.echo(report)


def _dedupe(posts: List[dict]) -> List[dict]:
    seen = set()
    out = []
    for p in posts:
        if p["id"] not in seen:
            seen.add(p["id"])
            out.append(p)
    return out


def _build_markdown(topic: str, subreddits: List[str], threads: List[dict]) -> str:
    subs_str = ", ".join(f"r/{s}" for s in subreddits)
    date_str = datetime.now().strftime("%Y-%m-%d")

    sections = [
        f"# Reddit Research: {topic}",
        f"Subreddits: {subs_str}",
        f"Fetched: {date_str}",
        f"Threads: {len(threads)}",
        "",
        "---",
        "",
    ]

    sorted_threads = sorted(threads, key=lambda x: x["score"], reverse=True)

    for t in sorted_threads:
        header = f"## [{t['score']} pts] \"{t['title']}\""
        meta = f"r/{t['subreddit']} | {t['num_comments']} comments | {t['url']}"

        block = [header, meta]

        selftext = (t.get("selftext") or "").strip()
        if selftext:
            block.append(f"\nPost: {selftext}")

        comments = t.get("comments", [])
        if comments:
            block.append("\nTop comments:")
            for c in comments[:8]:
                block.append(f"- [{c['score']} pts] u/{c['author']}: {c['body']}")

        block.append("\n---")
        sections.append("\n".join(block))
        sections.append("")

    return "\n".join(sections)


def main():
    cli()
