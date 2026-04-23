# reddit-find

GTM research from Reddit communities. Discovers the right subreddits, pulls high-signal threads and comments, outputs structured markdown for AI analysis. No API key required.

Built for B2B GTM teams who need real buyer language, not synthetic AI-generated positioning. The tool fetches. Your AI analyzes.

## Why Reddit for GTM?

Reddit is where buyers vent unfiltered. No corporate polish, no LinkedIn posturing. When an SDR posts "cold email is dead, what actually works?" with 300 upvotes and 80 comments, that thread contains more usable buyer language than any industry report.

**What reddit-find surfaces:**
- Exact phrases prospects use to describe their pain (cold email subject line gold)
- Which tools/competitors people actually recommend vs. complain about
- Objections buyers raise before they ever talk to sales
- Content angles that already have proven engagement
- ICP archetypes based on who's posting and what they're trying to solve

## Install

```bash
pip install reddit-find
```

No required API keys. Zero per-query cost.

**Optional** (improves subreddit discovery):
```bash
export SERPER_API_KEY="your_key"   # serper.dev, 2,500 free searches/month
```

## Quick Start

```bash
# Targeted: keyword search across Reddit history (specific pain phrase)
reddit-find search "merchant cash advance debt" -s smallbusiness --titles-only -o scan.md

# Broad: hot/top posts from known subs (landscape scan)
reddit-find fetch "b2b cold email" -s sales --titles-only -o scan.md

# Deep-dive a specific post + all comments
reddit-find post https://reddit.com/r/sales/comments/1abc23/title/ -o post.md
```

## Research Workflow

Three commands, three distinct data surfaces. The standard flow: **find threads → eval titles → deep dive winners**.

```
search or fetch  →  eval titles (Claude scores HIGH/SKIP)  →  post (full thread + comments)
```

Titles scan: 5-10 seconds. Full comment fetch on 40 posts: 80+ seconds. Scan first, pay the rate limit only on posts worth reading.

---

### Step 1: Find threads

**Use `search` when you have a specific pain phrase** — finds posts by keyword across Reddit's full history, not just what's trending today.

```bash
# Scoped to subreddits
reddit-find search "merchant cash advance" -s smallbusiness -s Entrepreneur \
  --titles-only -o scan.md

# Global search (all of Reddit)
reddit-find search "SDR quota attainment" --titles-only --sort top -o scan.md
```

**Use `fetch` when you want the current landscape** — pulls hot + top posts from subreddits. Good for "what's the ICP talking about right now."

```bash
reddit-find fetch "pipeline generation" -s sales -s b2bmarketing -s SaaS \
  --titles-only --max-age-days 365 -o scan.md
```

---

### Step 2: Eval titles

Read the scan output. Score each row:

- **HIGH**: title signals buyer pain/frustration/comparison/venting AND (score >50 OR comments >30)
- **SKIP**: memes, off-topic, humor posts, obvious self-promotion

The comments column is often more predictive than score — a 3-upvote post with 80 comments is a dogpile of shared pain.

---

### Step 3: Deep-dive selected posts

```bash
reddit-find post https://reddit.com/r/sales/comments/1abc23/ -o post-1.md
reddit-find post https://reddit.com/r/sales/comments/1xyz99/ -o post-2.md
```

Returns full post body + up to 50 comments ranked by upvotes. This is where the best EDP language lives — OP writes 3 sentences, comments are 40 people describing the same pain in their own words.

Feed the output to Claude, ChatGPT, or any AI for extraction.

## GTM Use Cases

### 1. Cold Email Hook Mining

Find the exact words prospects use to describe their problem. These become subject lines and opening lines that feel like mind-reading.

```bash
# Keyword-targeted: search across history for specific pain language
reddit-find search "outbound is dead" -s sales -s sdr --titles-only -o scan.md
# Deep-dive high-signal posts, then extract:
# - Pain phrases for subject lines
# - Objections to preempt in email body
# - Trigger events that make prospects ready to buy
```

**Example output your AI extracts:** `"I've sent 5,000 cold emails this quarter and booked 3 meetings"` - that's a hook. Your email opens with: *"Most SDRs send 5,000 emails to book 3 meetings. Here's what the top 1% do differently."*

### 2. ICP Pain Point Discovery

New market? New vertical? Reddit tells you what the actual problems are before you guess.

```bash
reddit-find fetch "HR software frustration" -s humanresources -s hrtechnology \
  --min-score 30 --max-age-days 365 -o hr-pain.md
```

Your AI extracts: specific pain points ranked by engagement, the job titles posting, what solutions they've tried and rejected, and what "good enough" looks like to them.

### 3. Competitor Intelligence

What do real users say about your competitors when they're not on a sales call?

```bash
reddit-find search "Clay vs Apollo" -s sales -s b2bmarketing --titles-only -o scan.md
reddit-find search "[competitor name] problems" -s relevant_sub --titles-only -o scan.md
```

Surfaces: feature gaps users actually care about, pricing objections, switching triggers, and the exact moment someone decides to look for alternatives.

### 4. Content Angle Discovery

Stop guessing what content to create. Find topics with proven engagement and write about those.

```bash
reddit-find fetch "LinkedIn outreach" -s sales -s LinkedInTips --titles-only -o content-scan.md
```

Threads with 200+ upvotes = validated content angles. Your AI turns each high-signal thread into a LinkedIn post brief, newsletter topic, or blog outline with built-in proof of demand.

### 5. Offer Validation

Before you build a new offer, check if the market actually wants it.

```bash
reddit-find search "fractional CMO" -s marketing -s startups -s Entrepreneur --titles-only -o scan.md
```

If the threads are full of "I wish someone would just..." or "why doesn't anyone offer..." - you've got signal. If it's crickets or negative sentiment, you just saved months of building the wrong thing.

### 6. Voice of Customer for Messaging

Stop writing copy that sounds like a marketer. Start writing copy that sounds like your buyer.

```bash
reddit-find fetch "CRM is a nightmare" -s sales -s salesforce -s hubspot \
  --min-score 50 -o voice.md
```

Extract verbatim phrases, metaphors, and complaints. Use them directly in landing pages, ads, and sales decks. When a prospect reads your copy and thinks "this person gets it" - that's the power of real VOC data.

### 7. Signal Detection for Outbound Timing

Reddit surfaces buying signals in real-time: team expansions, tool migrations, funding-driven hiring.

```bash
reddit-find fetch "switching from HubSpot" -s salesforce -s sales --max-age-days 30 -o signals.md
reddit-find fetch "just raised series A" -s startups --titles-only --max-age-days 7 -o funding.md
```

## Pre-Built Subreddit Clusters

Skip discovery for common GTM research. Copy-paste the right subs for your topic.

| Research Topic | Primary Subs | Secondary Subs |
|---|---|---|
| B2B cold outreach / SDR pain | `sales`, `b2bmarketing`, `sdr` | `b2b_sales`, `SaaSSales`, `Entrepreneur` |
| Cold email specifically | `sales`, `emailmarketing`, `b2bmarketing` | `sdr`, `growthHacking` |
| SaaS churn / customer success | `CustomerSuccess`, `SaaS` | `startups`, `saasmarketing` |
| SaaS growth / pipeline | `SaaS`, `saasmarketing`, `startups` | `Entrepreneur`, `sales` |
| LinkedIn / social selling | `sales`, `LinkedInTips`, `b2bmarketing` | `linkedin`, `sdr` |
| Marketing ops / RevOps | `marketing`, `b2bmarketing`, `salesforce` | `hubspot`, `RevOps` |
| Founder / early-stage GTM | `startups`, `Entrepreneur`, `SaaS` | `smallbusiness`, `growthhacking` |
| Agency / consulting | `consulting`, `marketing`, `freelance` | `agency`, `Entrepreneur` |
| Recruiting / hiring signals | `recruiting`, `humanresources` | `jobs`, `cscareerquestions` |
| Product-led growth | `SaaS`, `ProductManagement` | `saasmarketing`, `startups` |
| Data / analytics buyers | `datascience`, `analytics`, `BusinessIntelligence` | `dataengineering`, `SQL` |
| Fintech buyers | `fintech`, `personalfinance` | `investing`, `smallbusiness` |
| E-commerce / DTC | `ecommerce`, `Entrepreneur` | `shopify`, `digitalnomad` |
| HR tech / people ops | `humanresources`, `hrtechnology` | `recruiting`, `PeopleAnalytics` |
| IT / security buyers | `sysadmin`, `netsec`, `ITManagers` | `cybersecurity`, `devops` |
| Developer tools | `programming`, `devops`, `webdev` | `ExperiencedDevs`, `SoftwareEngineering` |

## Commands Reference

### `reddit-find search [OPTIONS] QUERY`

Search Reddit by keyword. Hits Reddit's search index — finds posts across history by relevance, not just current hot/top. Defaults tuned for EDP mining.

```
  QUERY                    Keyword or phrase to search for
  -s, --subreddit TEXT     Scope to subreddit (repeatable). Omit for global.
  --titles-only            Skip comments - titles, scores, dates, URLs only
  --max-age-days INT       Filter posts older than N days (default: 1825 / 5yr)
  --min-score INT          Min upvote score (default: 1)
  --limit INT              Posts per subreddit or total global (default: 50)
  --sort TEXT              relevance | top | new | comments (default: relevance)
  -o, --output TEXT        Save output to file (default: stdout)
```

### `reddit-find fetch [OPTIONS] TOPIC`

Fetch hot + top threads from subreddits. Auto-discovers subs or targets specific ones.

```
  TOPIC                    What you're researching
  -s, --subreddit TEXT     Target subreddit (repeatable, skips discovery)
  --titles-only            Skip comments - titles, scores, dates, URLs only
  --max-age-days INT       Filter posts older than N days (default: 365)
  --min-score INT          Min upvote score (default: 5)
  --top-threads INT        Top threads per sub (default: 8)
  --posts-per-sub INT      Posts to fetch per sub (default: 20)
  --serper-key TEXT        SerperDev API key (env: SERPER_API_KEY)
  -o, --output TEXT        Save output to file (default: stdout)
```

### `reddit-find post [OPTIONS] POST_REF`

Fetch a single post + all comments (up to 50). Use after eval step to deep-dive high-signal threads.

```
  POST_REF                 Full Reddit URL or bare post ID
  --sub TEXT               Subreddit name (required for bare IDs)
  -o, --output TEXT        Save output to file (default: stdout)
```

### `reddit-find discover TOPIC`

Find relevant subreddits for a topic. Uses Reddit native search + optional SerperDev.

```
  --serper-key TEXT        SerperDev API key (env: SERPER_API_KEY)
  --top INT                Number of subreddits to return (default: 8)
```

## Output Format

Structured markdown that any AI can parse directly.

**Full fetch output:**
```markdown
# Reddit Research: b2b cold email
Subreddits: r/sales, r/b2bmarketing
Fetched: 2026-04-22
Threads: 12

---

## [342 pts] "Title of post here"
r/sales | 45 comments | https://reddit.com/...
Post: {selftext}

Top comments:
- [89 pts] u/author: comment text here
- [45 pts] u/author: comment text here

---
```

**Titles-only scan:**
```markdown
# Reddit Posts: b2b cold email (titles scan)
Subreddits: r/sales, r/b2bmarketing
Posts: 24

| Score | Comments | Date | Title | URL |
|-------|----------|------|-------|-----|
| 342 | 45 | 2026-03-15 | "Cold email is dead..." | https://... |
```

## Claude Code Skill

Add reddit-find as a Claude Code skill (one-liner install):

```bash
curl -fsSL https://raw.githubusercontent.com/LeadGrowGTM/reddit-find/main/install-skill.sh | bash
```

This installs the skill into your `.claude/skills/` directory. Claude Code will automatically use the two-pass workflow, recency filtering, and GTM subreddit clusters when you ask it to research topics on Reddit.

## How It Works

1. **Find** - `search` hits Reddit's search index to find posts by keyword across history. `fetch` pulls current hot + top posts from subreddits. `discover` finds the right subreddits when you don't know where to look.
2. **Filter** - Recency filtering (`--max-age-days`), score thresholds (`--min-score`), and thread limits keep output focused.
3. **Eval** - `--titles-only` gives you a fast table of post titles, scores, comment counts, and URLs. Scan it, pick the winners.
4. **Deep dive** - `post` fetches the full thread: post body + up to 50 comments ranked by upvotes. That's where the real EDP language is.
5. **Output** - Structured markdown ready for any AI. Claude, ChatGPT, Gemini, local models — all work.

## Recency Guidance

Always filter by recency. Stale pain points produce stale copy.

| Scenario | Flag |
|----------|------|
| Default GTM research | `--max-age-days 365` |
| Recent trends | `--max-age-days 90` |
| This week / latest | `--max-age-days 7` |

## Cost

Zero. Reddit JSON API is free and requires no authentication. SerperDev is optional and has a free tier (2,500 searches/month).

## License

MIT - built by [LeadGrow](https://leadgrow.ai)
