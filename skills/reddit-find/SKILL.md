---
name: reddit-find
description: GTM research from Reddit — discover relevant subreddits, fetch top threads and comments as structured markdown. Claude in session reads the output and extracts pain points, buyer language, viral moments, ICP archetypes, and content angles. Use when researching ICP pain, finding cold email hooks, validating messaging, identifying content angles, or doing competitor research. No API key required. Triggers: Reddit research, buyer language, market pain, subreddit discovery, GTM intel, voice of customer, ICP validation, content angles from Reddit.
---

# reddit-find

Pure data fetcher for Reddit GTM research. Discovers subreddits, fetches top threads and comments, outputs structured markdown. Claude in session handles analysis — no Anthropic API key required.

## Install

```bash
pip install reddit-find
```

No required API keys. Optional:
```bash
export SERPER_API_KEY="your_serper_key"    # serper.dev — improves subreddit discovery
```

Get your SerperDev key at https://serper.dev (free tier: 2,500 searches/month). Without it, discovery uses Reddit's native search — works fine.

## Usage

### Full pipeline — fetch + Claude analyzes in session

```bash
reddit-find fetch "b2b cold email" -s sales --min-score 20 --top-threads 5 -o research.md
```

Then read the file in-session and extract GTM intel.

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
--subreddit / -s     Target specific subreddits (can use multiple, skips discovery)
--serper-key         SerperDev API key (optional, improves discovery)
--posts-per-sub      Posts to fetch per subreddit (default: 20)
--min-score          Minimum upvote score to include (default: 5)
--top-threads        Top threads to fetch per sub (default: 8)
--output / -o        Save output to file
```

## What the output looks like

```markdown
# Reddit Research: b2b cold email
Subreddits: r/sales, r/b2bmarketing
Fetched: 2026-04-22
Threads: 12

---

## [342 pts] "Title of post here"
r/sales | 45 comments | https://reddit.com/...
Post: {selftext if any}

Top comments:
- [89 pts] u/author: comment text here
- [45 pts] u/author: comment text here

---
```

## Claude's job after fetching

After running `reddit-find fetch`, read the output and extract:

1. **Pain Points** — what are people actually struggling with? Quote verbatim with score attribution.
2. **Buyer Language** — exact phrases ready for cold email subject lines and hooks. Format: `"[exact phrase]"`
3. **Viral Moments** — threads with outsized engagement. Why did it hit?
4. **ICP Archetypes** — who's posting? Their role, situation, what they're trying to solve.
5. **Tool & Competitor Mentions** — what tools come up, and what's the sentiment?
6. **Content Angles** — 5 specific post ideas derived from actual thread language.

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
2. Read the markdown output
3. Extract pain points + buyer language (verbatim quotes are gold)
4. Use viral thread titles as content hook templates
5. Save research to `leadgrow-hq/campaigns/leadgrow/` or client research folder

## Cost

No API costs. Reddit JSON API is free. SerperDev optional — free tier covers 2,500 searches/month.
