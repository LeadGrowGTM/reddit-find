---
name: reddit-find
description: GTM research from Reddit — discover relevant subreddits via Google, fetch top threads, extract pain points, buyer language, viral moments, ICP archetypes, and content angles. Use when researching ICP pain, finding cold email hooks from buyer language, validating messaging, identifying content angles, or doing competitor research. Triggers: Reddit research, buyer language, market pain, subreddit discovery, GTM intel, voice of customer, ICP validation, content angles from Reddit.
---

# reddit-find

Surface GTM intelligence from Reddit communities. Finds the right subreddits, pulls high-signal threads, and extracts structured research — pain points, verbatim buyer language, viral moments, and content angles.

## Install

```bash
pip install reddit-find
```

Required env vars:
```bash
export SERPER_API_KEY="your_serper_key"    # serper.dev — for subreddit discovery
export ANTHROPIC_API_KEY="your_key"         # for analysis
```

Get your SerperDev key at https://serper.dev (free tier: 2,500 searches/month).

## Usage

### Full pipeline — topic to report

```bash
reddit-find fetch "b2b cold email pain points" -o research.md
```

Discovers subreddits → fetches hot + top threads → pulls comments → Claude analysis → saves report.

### Skip discovery, target known subs

```bash
reddit-find fetch "pipeline generation" -s sales -s b2bmarketing -s sdr -o pipeline-pain.md
```

### Just discover subreddits

```bash
reddit-find discover "SaaS churn"
```

### Options

```
--subreddit / -s     Target specific subreddits (can use multiple, skips SerperDev)
--posts-per-sub      Posts to fetch per subreddit (default: 20)
--min-score          Minimum upvote score to include (default: 5)
--top-threads        Top threads to analyze per sub (default: 8)
--output / -o        Save report to file
--model              Claude model (default: claude-haiku-4-5-20251001)
```

## What Claude gets back

Structured markdown with:

- **Pain Points** — verbatim quotes with attribution + score
- **Buyer Language** — exact phrases ready for cold email subject lines and hooks
- **Viral Moments** — high-engagement threads with "why it hit" analysis
- **ICP Archetypes** — role, situation, and what they're trying to solve
- **Tool & Competitor Mentions** — with sentiment
- **Content Angles** — 5 specific post ideas derived from actual thread language

## When to use

| Situation | Command |
|-----------|---------|
| Writing cold email for a new ICP | `reddit-find fetch "<ICP problem>" -o buyer-language.md` |
| Content batch for a new topic | `reddit-find fetch "<topic>" -s <sub> -o angles.md` |
| Researching a competitor | `reddit-find fetch "<competitor name>" -s <relevant_sub>` |
| Validating a new offer angle | `reddit-find fetch "<offer premise>" -o validation.md` |
| State of Market report | `reddit-find fetch "<market>" -s <sub1> -s <sub2> -o som.md` |

## Workflow

1. Run `reddit-find fetch "<topic>" -o research.md`
2. Read pain points + buyer language sections first
3. Pull 3-5 verbatim quotes into cold email copy
4. Use viral thread titles as content hook templates
5. Save report to `leadgrow-hq/campaigns/leadgrow/` or client research folder

## Cost

Analysis uses Claude Haiku by default — roughly $0.002-0.005 per run. SerperDev free tier covers 2,500 discovery searches/month.
