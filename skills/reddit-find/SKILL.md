---
name: reddit-find
description: GTM research from Reddit. Three commands: `search` (keyword search across Reddit history — use when researching specific pain like "MCA debt" or "cold email is dead"), `fetch` (top/hot posts from known subs — use for broad ICP landscape), `post` (deep dive single thread). Two-pass workflow: Pass 1 scan titles fast (--titles-only), Pass 2 deep-dive with `post`. Built-in recency filter. Pre-built GTM subreddit clusters. No API key required. Gemini CLI fallback when Reddit API is blocked.
---

# reddit-find

Pure data fetcher for Reddit GTM research. Three commands cover the full research workflow: `search` for targeted keyword mining, `fetch` for broad subreddit scanning, `post` for deep thread dives. Claude in session handles analysis — no Anthropic API key required.

## Install

```bash
pip install -e C:/Users/mitch/Everything_CC/reddit-find/
```

No required API keys. Optional:
```bash
export SERPER_API_KEY="your_serper_key"    # serper.dev — improves subreddit discovery
```

## Commands

### `search` — Keyword search across Reddit history

Use when you know the pain phrase. Hits Reddit's search endpoint — finds posts by keyword in title/body across all of history, not just current hot/top.

```bash
# Targeted EDP mining — finds posts wherever they exist historically
reddit-find search "merchant cash advance" -s smallbusiness --titles-only -o /tmp/scan.md
reddit-find search "MCA debt payments" -s smallbusiness -s Entrepreneur --max-age-days 730
reddit-find search "cold email is dead" --sort top --limit 50 --titles-only

# Global search (no subreddit scoping)
reddit-find search "b2b SDR burnout" --titles-only --max-age-days 365
```

**Options:**
```
--subreddit / -s     Scope to specific subreddits (multiple OK). Omit for global.
--max-age-days N     Filter posts older than N days (default: 365)
--min-score N        Minimum upvote score (default: 5)
--limit N            Posts to fetch per subreddit / total global (default: 25)
--sort               relevance | top | new | comments (default: relevance)
--titles-only        Skip comments — just titles, scores, dates, URLs
--output / -o        Save output to file
```

**When to use search vs fetch:**
- `search` — you have a specific pain phrase or keyword to mine ("merchant cash advance debt", "SDR quota missed"). Finds historical posts by relevance.
- `fetch` — you want to see what's trending in a sub right now (hot + top posts). Good for broad ICP landscape.

### `fetch` — Hot/top posts from known subs

```bash
# Pass 1: titles-only scan (fast, decide what to deep-dive)
reddit-find fetch "<topic>" -s <sub> --titles-only --max-age-days 365 -o /tmp/scan.md

# Pass 2 prep: full fetch with comments on top threads
reddit-find fetch "<topic>" -s <sub> --max-age-days 365 --min-score 50 --top-threads 3 -o /tmp/full.md
```

**Options:**
```
--subreddit / -s     Target specific subreddits (multiple OK, skips discovery)
--max-age-days N     Filter posts older than N days (default: 365)
--titles-only        Skip comments — just titles, scores, dates, URLs
--min-score N        Minimum upvote score (default: 5)
--top-threads N      Top threads to fetch per sub (default: 8)
--posts-per-sub N    Posts to fetch per sub before filtering (default: 20)
--output / -o        Save output to file
```

### `post` — Single-post deep dive

```bash
reddit-find post https://reddit.com/r/sales/comments/1abc23/title/ -o /tmp/post.md
reddit-find post 1abc23 --sub sales -o /tmp/post.md
```

Fetches the full thread: post body + all comments (up to 50). Use after a titles scan to deep-dive high-signal posts.

### `discover` — Find subreddits

```bash
reddit-find discover "b2b cold email"
```

---

## Recency Guidance

Always filter by recency. Stale pain points produce stale copy.

| Scenario | Flag |
|----------|------|
| Default GTM research | `--max-age-days 365` |
| "Recent trends" / "what's happening now" | `--max-age-days 90` |
| "This week" / "latest" | `--max-age-days 7` |

**Never skip recency filtering for GTM research.**

---

## Standard Workflow (Two-Pass + Optional Search)

### Option A: Targeted EDP mining (use `search`)

When you have a specific pain phrase — "merchant cash advance", "SDR burnout", "churn rate" — use `search` so you find posts from across Reddit's history, not just current hot.

```bash
# Pass 1 — keyword scan
reddit-find search "<pain phrase>" -s <sub1> -s <sub2> --titles-only --max-age-days 730 -o /tmp/scan.md

# Pass 2 — deep dive on selected posts
reddit-find post <url-from-scan> -o /tmp/post-1.md
reddit-find post <url-from-scan> -o /tmp/post-2.md
```

### Option B: Broad ICP landscape (use `fetch`)

When you want to see what's trending in a subreddit right now — no specific search term.

```bash
# Pass 1 — hot/top titles scan
reddit-find fetch "<topic>" -s <sub1> -s <sub2> --titles-only --max-age-days 365 -o /tmp/scan.md

# Pass 2 — deep dive on selected posts
reddit-find post <url-from-scan> -o /tmp/post-1.md
reddit-find post <url-from-scan> -o /tmp/post-2.md
```

### Scoring guide (Pass 1)

Read the scan output. Score each post:
- **HIGH**: >200 pts OR >50 comments AND title signals buyer pain/frustration/comparison/venting
- **SKIP**: memes, humor posts, off-topic, <20 pts, obvious jokes

**Why two passes:** Comment fetching is slow (2s sleep per post). On a 5-sub scan with 8 threads each, fetching all comments takes 80+ seconds. Titles scan takes 5-10 seconds. Read first, fetch deep only what matters.

---

## Pre-Built GTM Subreddit Clusters

Use these instead of running `discover` for common research topics.

| Research Topic | Primary Subs | Secondary Subs |
|---|---|---|
| B2B cold outreach / SDR pain | `sales`, `b2bmarketing`, `sdr` | `b2b_sales`, `SaaSSales`, `Entrepreneur` |
| Cold email specifically | `sales`, `emailmarketing`, `b2bmarketing` | `sdr`, `growthHacking` |
| SaaS churn / customer success | `CustomerSuccess`, `SaaS` | `startups`, `saasmarketing` |
| SaaS growth / pipeline generation | `SaaS`, `saasmarketing`, `startups` | `Entrepreneur`, `sales` |
| LinkedIn outreach / social selling | `sales`, `LinkedInTips`, `b2bmarketing` | `linkedin`, `sdr` |
| Marketing ops / RevOps | `marketing`, `b2bmarketing`, `salesforce` | `hubspot`, `RevOps` |
| Founder / early-stage GTM | `startups`, `Entrepreneur`, `SaaS` | `smallbusiness`, `growthhacking` |
| Agency / consulting pain | `consulting`, `marketing`, `freelance` | `agency`, `Entrepreneur` |
| Recruiting / hiring signal | `recruiting`, `humanresources` | `jobs`, `cscareerquestions` |
| Product-led growth / PLG | `SaaS`, `ProductManagement` | `saasmarketing`, `startups` |
| Data / analytics buyers | `datascience`, `analytics`, `BusinessIntelligence` | `dataengineering`, `SQL` |
| Fintech / finance buyers | `fintech`, `personalfinance` | `investing`, `smallbusiness` |
| E-commerce / DTC pain | `ecommerce`, `Entrepreneur` | `shopify`, `digitalnomad` |
| HR tech / people ops | `humanresources`, `hrtechnology` | `recruiting`, `PeopleAnalytics` |
| IT / security buyers | `sysadmin`, `netsec`, `ITManagers` | `cybersecurity`, `devops` |
| Developer tools | `programming`, `devops`, `webdev` | `ExperiencedDevs`, `SoftwareEngineering` |

---

## Claude's Job After Fetching

After reading the output from `fetch` (full) or `post`:

1. **Pain Points** — what are people actually struggling with? Quote verbatim with score attribution.
2. **Buyer Language** — exact phrases ready for cold email subject lines and hooks. Format: `"[exact phrase]"`
3. **Viral Moments** — threads with outsized engagement relative to sub size. Why did it hit?
4. **ICP Archetypes** — who's posting? Their role, situation, what they're trying to solve.
5. **Tool & Competitor Mentions** — what comes up, and what's the sentiment?
6. **Content Angles** — 5 specific post ideas derived from actual thread language.

---

## When to Use

| Situation | Command |
|-----------|---------|
| You have a specific pain phrase to mine | `search "<phrase>" -s <sub> --titles-only` then `post` |
| New ICP — find pain and buyer language | `search "<ICP problem>" -s <sub> --titles-only` then `post` |
| Broad ICP landscape / what's trending | `fetch "<topic>" -s <sub> --titles-only` then `post` |
| Cold email hooks for a specific market | `search "<ICP problem>" --sort top --titles-only` then `post` |
| Content batch for a new topic | `fetch "<topic>" -s <sub> --titles-only` then `post` high-signal |
| Researching a competitor | `search "<competitor name>" -s <relevant_sub>` |
| Validating a new offer angle | `search "<offer premise>" --titles-only` |
| Voice of market for playbook research | Full `fetch`, 3-5 subs, `--max-age-days 365` |

---

## Example: Targeted EDP Mining (search-first)

```bash
# Pass 1 — keyword scan for specific pain phrase
reddit-find search "merchant cash advance" -s smallbusiness -s Entrepreneur \
  --titles-only --max-age-days 730 -o /tmp/scan.md

# Claude reads scan.md, marks HIGH-signal posts

# Pass 2 — deep dive on 2-3 selected posts
reddit-find post https://reddit.com/r/smallbusiness/comments/1abc23/ -o /tmp/post-1.md
reddit-find post https://reddit.com/r/Entrepreneur/comments/1xyz99/ -o /tmp/post-2.md

# Claude reads post-1.md and post-2.md and extracts full GTM intel
```

## Example: Broad ICP Landscape (fetch-first)

```bash
# Pass 1 — scan hot/top across core GTM subs
reddit-find fetch "b2b cold email" -s sales -s b2bmarketing -s sdr \
  --titles-only --max-age-days 365 -o /tmp/scan.md

# Pass 2 — deep dive on 2-3 selected posts
reddit-find post https://reddit.com/r/sales/comments/1abc23/ -o /tmp/post-1.md
reddit-find post https://reddit.com/r/sales/comments/1xyz99/ -o /tmp/post-2.md
```

---

## Gemini CLI Fallback

If `reddit-find` returns empty results, HTTP 429, or consistent errors, fall back to Gemini CLI (can browse Reddit directly):

```bash
tmux new-session -d -s gemini_reddit -x 200 -y 50
tmux send-keys -t gemini_reddit 'gemini' Enter
sleep 3
tmux send-keys -t gemini_reddit 'Browse reddit.com/r/sales/hot and summarize the top 10 posts with scores and key quotes from comments' Enter
sleep 45
tmux capture-pane -t gemini_reddit -p -S -500
tmux kill-session -t gemini_reddit
```

Customize the prompt: replace `r/sales/hot` with the subreddit and sort you need. Gemini reads the live Reddit page and returns structured results. Use when the JSON API is blocked or rate-limited.

---

## Cost

No API costs. Reddit JSON API is free. SerperDev optional — free tier covers 2,500 searches/month.
