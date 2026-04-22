"""Claude-powered GTM intelligence extraction from Reddit threads."""

from typing import Dict, List

import anthropic

SYSTEM_PROMPT = """You are a GTM research analyst extracting buyer intelligence from Reddit.
Your job: identify the SIGNAL in community conversations — what people actually say when they're frustrated, evaluating tools, or venting about their jobs.
Be ruthlessly specific. No padding. Every output should be immediately usable in a cold email, content post, or campaign."""

EXTRACT_PROMPT = """Reddit threads from {subreddits} on topic: "{topic}"

Extract GTM intelligence using this exact structure. Pull verbatim quotes where possible — the buyer's actual words beat your paraphrase every time.

---

## Pain Points
What are people actually struggling with? Quote them directly.
Format: > "[quote]" — r/{sub}, {score} pts

## Buyer Language (Copy-Ready Phrases)
Exact phrases buyers use. These go directly into subject lines, hooks, and CTAs.
Format: - "[exact phrase]"

## Viral Moments
Threads with outsized engagement signal that the market cares deeply about this.
Format: - **[title]** — {score} pts, {comments} comments | Why it hit: [1 sentence]

## ICP Archetypes
Who's posting? Map their role, situation, and what they're trying to solve.
Format: - **[Role/Title]:** [their situation in 1-2 sentences]

## Tool & Competitor Mentions
What tools and vendors come up? What's the sentiment?
Format: - **[Tool]:** [context + sentiment]

## Content Angles
5 specific post ideas directly derived from thread language. Actionable, not generic.
Format: - **[angle type]:** [specific brief — what the post says and why it'll land]

---

Threads:

{threads}"""


def analyze_threads(
    threads: List[Dict],
    topic: str,
    subreddits: List[str],
    api_key: str,
    model: str = "claude-haiku-4-5-20251001",
) -> str:
    """Extract structured GTM intel from Reddit threads using Claude."""
    threads_text = _format_threads(threads)
    subs_str = ", ".join(f"r/{s}" for s in subreddits)

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=model,
        max_tokens=2500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": EXTRACT_PROMPT.format(
                    topic=topic,
                    subreddits=subs_str,
                    threads=threads_text,
                ),
            }
        ],
    )

    return message.content[0].text


def _format_threads(threads: List[Dict]) -> str:
    blocks = []
    for t in threads:
        lines = [
            f"**[{t['score']} pts | {t['num_comments']} comments] {t['title']}**",
            f"r/{t['subreddit']} | {t.get('url', '')}",
        ]
        if t.get("selftext", "").strip():
            lines.append(f"Post body: {t['selftext'][:400]}")
        comments = t.get("comments", [])
        if comments:
            lines.append("Top comments:")
            for c in comments[:6]:
                lines.append(f"  [{c['score']} pts] u/{c['author']}: {c['body'][:300]}")
        blocks.append("\n".join(lines))
    return "\n\n---\n\n".join(blocks)
