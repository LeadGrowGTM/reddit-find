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
from .fetch import fetch_post_comments, fetch_single_post, fetch_subreddit_posts, search_posts


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
@click.option("--max-age-days", default=365, show_default=True, help="Filter posts older than N days (default: 365). Use 90 for 'recent', 7 for 'this week'.")
@click.option("--titles-only", is_flag=True, default=False, help="Skip comments — return post titles, scores, dates, and URLs only. Fast scan to decide which posts to deep-dive.")
@click.option("--output", "-o", default=None, help="Save output to file (default: stdout)")
def fetch(
    topic: str,
    serper_key: Optional[str],
    subreddit: tuple,
    posts_per_sub: int,
    min_score: int,
    top_threads: int,
    max_age_days: int,
    titles_only: bool,
    output: Optional[str],
):
    """Fetch Reddit threads and output structured markdown for analysis.

    TOPIC: What you're researching (e.g. "b2b pipeline generation")

    No API key required. Output is structured markdown — Claude reads it
    and extracts pain points, buyer language, viral moments, and content angles.

    \b
    Examples:
      reddit-find fetch "b2b cold email" -s sales --titles-only --max-age-days 90 -o scan.md
      reddit-find fetch "b2b cold email" -s sales --min-score 20 --max-age-days 365 -o research.md
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

    # Step 2: Fetch posts (with recency filter applied inside fetch_subreddit_posts)
    all_threads = []
    for sub in target_subs:
        click.echo(f"Fetching r/{sub}...", err=True)

        hot = fetch_subreddit_posts(sub, sort="hot", limit=posts_per_sub, max_age_days=max_age_days)
        top = fetch_subreddit_posts(sub, sort="top", limit=posts_per_sub, time_filter="month", max_age_days=max_age_days)
        posts = _dedupe(hot + top)
        posts = [p for p in posts if p["score"] >= min_score]
        posts = sorted(posts, key=lambda x: x["score"], reverse=True)[:top_threads]

        if titles_only:
            click.echo(f"  {len(posts)} posts", err=True)
        else:
            click.echo(f"  {len(posts)} threads (fetching comments...)", err=True)
            for post in posts:
                post["comments"] = fetch_post_comments(sub, post["id"]) or []

        all_threads.extend(posts)

    if not all_threads:
        click.echo("No threads fetched. Check subreddit names or lower --min-score.", err=True)
        sys.exit(1)

    # Step 3: Build structured markdown (no analysis — Claude handles that)
    if titles_only:
        click.echo(f"\nFetched {len(all_threads)} posts. Building titles scan...\n", err=True)
        report = _build_titles_markdown(topic, target_subs, all_threads)
    else:
        click.echo(f"\nFetched {len(all_threads)} threads. Building markdown...\n", err=True)
        report = _build_markdown(topic, target_subs, all_threads)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(report)
        click.echo(f"Saved to: {output}", err=True)
    else:
        click.echo(report)


@cli.command()
@click.argument("post_ref")
@click.option("--sub", default=None, help="Subreddit name (required when passing a bare post ID, optional for full URLs)")
@click.option("--output", "-o", default=None, help="Save output to file (default: stdout)")
def post(post_ref: str, sub: Optional[str], output: Optional[str]):
    """Fetch a single post + ALL its comments for deep analysis.

    POST_REF: Full Reddit URL or bare post ID (e.g. 1abc23)

    Use after a --titles-only scan to deep-dive into high-signal posts.

    \b
    Examples:
      reddit-find post https://reddit.com/r/sales/comments/1abc23/title/ -o post.md
      reddit-find post 1abc23 --sub sales -o post.md
    """
    click.echo(f"Fetching post: {post_ref}", err=True)
    result = fetch_single_post(post_ref, subreddit=sub)

    if not result:
        click.echo("Could not fetch post. Check the URL/ID or try --sub <subreddit>.", err=True)
        sys.exit(1)

    click.echo(f"  Fetched: \"{result['title']}\" ({len(result['comments'])} comments)", err=True)

    report = _build_post_markdown(result)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(report)
        click.echo(f"Saved to: {output}", err=True)
    else:
        click.echo(report)


@cli.command()
@click.argument("query")
@click.option("--subreddit", "-s", multiple=True, help="Scope search to specific subreddits (repeatable). Omit for global search.")
@click.option("--min-score", default=1, show_default=True, help="Minimum post score to include (default: 1 — keyword search returns relevant low-score posts)")
@click.option("--max-age-days", default=1825, show_default=True, help="Filter posts older than N days (default: 1825 / 5 years — search mines history)")
@click.option("--limit", default=50, show_default=True, help="Posts to fetch per subreddit (or total for global search)")
@click.option("--sort", default="relevance", show_default=True, type=click.Choice(["relevance", "top", "new", "comments"]), help="Reddit search sort order")
@click.option("--titles-only", is_flag=True, default=False, help="Return titles/scores/URLs only. Fast scan — feed high-signal URLs to `reddit-find post`.")
@click.option("--output", "-o", default=None, help="Save output to file (default: stdout)")
def search(
    query: str,
    subreddit: tuple,
    min_score: int,
    max_age_days: int,
    limit: int,
    sort: str,
    titles_only: bool,
    output: Optional[str],
):
    """Search Reddit for posts matching a keyword query.

    QUERY: Keyword or phrase to search for (e.g. "merchant cash advance debt")

    Uses Reddit's search endpoint — finds posts across history by keyword,
    not just current hot/top. Scoped to subreddits if -s flags given,
    otherwise global across all of Reddit.

    \b
    Examples:
      reddit-find search "merchant cash advance" -s smallbusiness --titles-only -o scan.md
      reddit-find search "MCA debt" -s smallbusiness -s Entrepreneur --max-age-days 730
      reddit-find search "cold email is dead" --sort top --limit 50 --titles-only
    """
    scope = f"r/{', r/'.join(subreddit)}" if subreddit else "all of Reddit"
    click.echo(f"Searching {scope} for: {query}", err=True)

    posts = search_posts(
        query=query,
        subreddits=list(subreddit) if subreddit else None,
        max_age_days=max_age_days,
        min_score=min_score,
        limit=limit,
        sort=sort,
    )

    if not posts:
        click.echo("No posts found. Try broader query, lower --min-score, or higher --max-age-days.", err=True)
        sys.exit(1)

    click.echo(f"Found {len(posts)} posts.", err=True)

    if titles_only:
        report = _build_titles_markdown(query, list(subreddit) if subreddit else ["all"], posts)
    else:
        for post in posts:
            sub = post.get("subreddit", "")
            post["comments"] = fetch_post_comments(sub, post["id"]) if sub else []
        report = _build_markdown(query, list(subreddit) if subreddit else ["all"], posts)

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


def _build_titles_markdown(topic: str, subreddits: List[str], threads: List[dict]) -> str:
    """Fast titles-only scan — no comments. Used for Pass 1 of two-pass workflow."""
    from datetime import datetime, timezone

    subs_str = ", ".join(f"r/{s}" for s in subreddits)
    date_str = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# Reddit Posts: {topic} (titles scan)",
        f"Subreddits: {subs_str}",
        f"Fetched: {date_str}",
        f"Posts: {len(threads)}",
        "",
        "| Score | Comments | Date | Title | URL |",
        "|-------|----------|------|-------|-----|",
    ]

    sorted_threads = sorted(threads, key=lambda x: x["score"], reverse=True)
    for t in sorted_threads:
        created_utc = t.get("created_utc", 0)
        if created_utc:
            post_date = datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d")
        else:
            post_date = "unknown"
        title = t["title"].replace("|", "-")
        lines.append(
            f"| {t['score']} | {t['num_comments']} | {post_date} | {title} | {t['url']} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Scoring guide (Claude)")
    lines.append("- **HIGH**: >200 pts OR >50 comments AND title signals buyer pain/frustration/comparison")
    lines.append("- **SKIP**: memes, off-topic, <20 pts, humor posts")
    lines.append("")
    lines.append("Deep-dive high-signal posts with: `reddit-find post <url> -o post.md`")

    return "\n".join(lines)


def _build_post_markdown(post: dict) -> str:
    """Full thread markdown for single-post deep dive."""
    title = post["title"]
    score = post["score"]
    sub = post.get("subreddit", "")
    url = post["url"]
    num_comments = post.get("num_comments", 0)
    post_date = post.get("post_date", "unknown")
    selftext = post.get("selftext", "").strip()
    comments = post.get("comments", [])

    lines = [
        f"# Deep Dive: \"{title}\"",
        f"r/{sub} | {score} pts | {num_comments} comments | {post_date}",
        f"URL: {url}",
        "",
        "---",
        "",
    ]

    if selftext:
        lines.append("## Post Body")
        lines.append(selftext)
        lines.append("")
        lines.append("---")
        lines.append("")

    if comments:
        lines.append(f"## Comments ({len(comments)} fetched)")
        lines.append("")
        for i, c in enumerate(comments, 1):
            lines.append(f"### [{c['score']} pts] u/{c['author']}")
            lines.append(c["body"])
            lines.append("")
    else:
        lines.append("*No comments found.*")

    return "\n".join(lines)


def main():
    cli()
