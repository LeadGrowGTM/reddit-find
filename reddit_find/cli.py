"""reddit-find CLI - GTM research from Reddit communities."""

import sys
from datetime import datetime
from typing import List, Optional

import click

from . import __version__
from .analyze import analyze_threads
from .discover import find_subreddits
from .fetch import fetch_post_comments, fetch_subreddit_posts


@click.group()
@click.version_option(version=__version__)
def cli():
    """reddit-find - surface GTM intel from Reddit communities.

    Discovers relevant subreddits, fetches top threads, and extracts
    pain points, buyer language, viral moments, and content angles.
    """
    pass


@cli.command()
@click.argument("topic")
@click.option("--serper-key", envvar="SERPER_API_KEY", required=True, help="SerperDev API key (serper.dev)")
@click.option("--top", default=8, show_default=True, help="Number of subreddits to return")
def discover(topic: str, serper_key: str, top: int):
    """Find relevant subreddits for a GTM topic.

    TOPIC: The topic or ICP problem to research (e.g. "b2b cold email")
    """
    click.echo(f"Searching for subreddits: {topic}\n")
    subreddits = find_subreddits(topic, serper_key, num_results=top)

    if not subreddits:
        click.echo("No subreddits found. Try a broader topic.", err=True)
        sys.exit(1)

    click.echo(f"Top subreddits for '{topic}':\n")
    for i, s in enumerate(subreddits, 1):
        bar = "#" * s["relevance_score"]
        click.echo(f"  {i:2}. r/{s['subreddit']:<30} {bar} ({s['relevance_score']})")

    click.echo(f"\nRun the full pipeline:")
    subs_flags = " ".join(f"-s {s['subreddit']}" for s in subreddits[:5])
    click.echo(f"  reddit-find fetch \"{topic}\" {subs_flags}")


@cli.command()
@click.argument("topic")
@click.option("--serper-key", envvar="SERPER_API_KEY", default=None, help="SerperDev API key (required unless -s is used)")
@click.option("--anthropic-key", envvar="ANTHROPIC_API_KEY", required=True, help="Anthropic API key")
@click.option("--subreddit", "-s", multiple=True, help="Target specific subreddits (skips discovery)")
@click.option("--posts-per-sub", default=20, show_default=True, help="Posts to fetch per subreddit")
@click.option("--min-score", default=5, show_default=True, help="Minimum post score to include")
@click.option("--top-threads", default=8, show_default=True, help="Top threads to analyze per subreddit")
@click.option("--output", "-o", default=None, help="Save report to file (default: stdout)")
@click.option("--model", default="claude-haiku-4-5-20251001", show_default=True, help="Claude model for analysis")
def fetch(
    topic: str,
    serper_key: Optional[str],
    anthropic_key: str,
    subreddit: tuple,
    posts_per_sub: int,
    min_score: int,
    top_threads: int,
    output: Optional[str],
    model: str,
):
    """Run full GTM research pipeline: discover -> fetch -> analyze.

    TOPIC: What you're researching (e.g. "b2b pipeline generation")

    \b
    Examples:
      reddit-find fetch "cold email pain points" -o research.md
      reddit-find fetch "SaaS churn" -s churnzero -s CustomerSuccess -o churn.md
    """
    # Step 1: Determine subreddits
    if subreddit:
        target_subs = list(subreddit)
        click.echo(f"Targeting: {', '.join(f'r/{s}' for s in target_subs)}\n")
    else:
        if not serper_key:
            click.echo(
                "Error: --serper-key (or SERPER_API_KEY) required for subreddit discovery.\n"
                "Alternatively, pass subreddits directly with -s <subreddit>",
                err=True,
            )
            sys.exit(1)
        click.echo(f"Discovering subreddits for: {topic}...")
        discovered = find_subreddits(topic, serper_key)
        if not discovered:
            click.echo("No subreddits found. Try passing -s <subreddit> directly.", err=True)
            sys.exit(1)
        target_subs = [s["subreddit"] for s in discovered[:5]]
        click.echo(f"Targeting: {', '.join(f'r/{s}' for s in target_subs)}\n")

    # Step 2: Fetch posts + comments
    all_threads = []
    for sub in target_subs:
        click.echo(f"Fetching r/{sub}...")
        posts = []

        hot = fetch_subreddit_posts(sub, sort="hot", limit=posts_per_sub)
        top = fetch_subreddit_posts(sub, sort="top", limit=posts_per_sub, time_filter="month")
        posts = _dedupe(hot + top)
        posts = [p for p in posts if p["score"] >= min_score]
        posts = sorted(posts, key=lambda x: x["score"], reverse=True)[:top_threads]

        click.echo(f"  {len(posts)} threads (fetching comments...)")
        for post in posts:
            post["comments"] = fetch_post_comments(sub, post["id"]) or []

        all_threads.extend(posts)

    if not all_threads:
        click.echo("No threads fetched. Check subreddit names or lower --min-score.", err=True)
        sys.exit(1)

    click.echo(f"\nAnalyzing {len(all_threads)} threads with Claude ({model})...")

    # Step 3: Analyze
    analysis = analyze_threads(all_threads, topic, target_subs, anthropic_key, model=model)

    # Step 4: Build + output report
    report = _build_report(topic, target_subs, all_threads, analysis)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(report)
        click.echo(f"\nReport saved: {output}")
    else:
        click.echo("\n" + "=" * 60 + "\n")
        click.echo(report)


def _dedupe(posts: List[dict]) -> List[dict]:
    seen = set()
    out = []
    for p in posts:
        if p["id"] not in seen:
            seen.add(p["id"])
            out.append(p)
    return out


def _build_report(topic: str, subreddits: List[str], threads: List[dict], analysis: str) -> str:
    subs_str = ", ".join(f"r/{s}" for s in subreddits)
    date_str = datetime.now().strftime("%Y-%m-%d")
    thread_list = "\n".join(
        f"- [{t['score']} pts] [{t['title']}]({t['url']}) - r/{t['subreddit']}"
        for t in sorted(threads, key=lambda x: x["score"], reverse=True)[:15]
    )

    return f"""---
title: Reddit GTM Research - {topic}
subreddits: {subs_str}
threads_analyzed: {len(threads)}
generated: {date_str}
tool: reddit-find (github.com/LeadGrowGTM/reddit-find)
---

# Reddit GTM Research: {topic}

**Subreddits:** {subs_str}
**Threads analyzed:** {len(threads)}
**Generated:** {date_str}

---

{analysis}

---

## Source Threads

{thread_list}
"""


def main():
    cli()
