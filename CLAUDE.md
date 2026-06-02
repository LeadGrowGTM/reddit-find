# reddit-find

GTM research tool. Fetches Reddit threads and comments as structured markdown — buyer language, pain points, objections, content angles. No Reddit API key required.

## Install

```bash
# From the repo root (editable, recommended for local work)
pip install -e .

# Or from PyPI
pip install reddit-find
```

**Optional env var** (improves subreddit discovery via Google):
```bash
# In C:/Users/mitch/Everything_CC/.env or the repo root .env
SERPER_API_KEY=your_key   # serper.dev — 2,500 free searches/month
```
The tool auto-loads `.env` from both the repo root and `C:/Users/mitch/Everything_CC/.env`. No other keys required.

## Three Commands

### 1. `search` — keyword search across Reddit history
Use when you have a specific pain phrase. Searches Reddit's full post history, not just what's trending.

```bash
# Scoped to subreddits (can repeat -s)
reddit-find search "merchant cash advance debt" -s smallbusiness -s Entrepreneur --titles-only -o scan.md

# Global (all of Reddit)
reddit-find search "cold email is dead" --sort top --limit 50 --titles-only -o scan.md

# Deeper history window
reddit-find search "SDR quota attainment" --max-age-days 730 --titles-only -o scan.md
```

### 2. `fetch` — hot/top posts from known subreddits
Use when you want the current ICP landscape. Pulls hot + top posts from specified subs.

```bash
reddit-find fetch "b2b pipeline generation" -s sales -s b2bmarketing -s SaaS --titles-only -o scan.md

# With comments (slower — ~80s for 40 posts)
reddit-find fetch "b2b cold email" -s sales --min-score 20 --max-age-days 365 -o research.md
```

### 3. `post` — deep-dive a single thread
Use after a titles scan. Fetches full post body + up to 50 comments ranked by upvotes.

```bash
reddit-find post https://reddit.com/r/sales/comments/1abc23/title/ -o post-1.md

# With bare post ID
reddit-find post 1abc23 --sub sales -o post.md
```

### 4. `discover` — find relevant subreddits
Use when you don't know which subs to target.

```bash
reddit-find discover "b2b cold email"
# Prints top subreddits + a ready-to-run fetch command
```

## Standard Research Workflow

```
1. search or fetch --titles-only → scan.md   (5-10 seconds, title table)
2. Read scan.md. Score each row: HIGH (buyer pain, >50pts or >30 comments) vs SKIP
3. reddit-find post <url> -o post-N.md       (one per HIGH thread)
4. Feed post-N.md files to Claude for extraction
```

The comments column beats score — a 3-upvote post with 80 comments is 80 people describing the same pain.

## Output Format

All commands write structured markdown:

- `--titles-only`: markdown table (Score | Comments | Date | Title | URL) + Claude scoring guide appended
- Full fetch: H2 per thread, top 8 comments per thread
- `post`: Full body + all comments as H3 blocks sorted by upvotes

Default output is stdout. Use `-o filename.md` to write to file.

## Key Flags

| Flag | Default | Notes |
|------|---------|-------|
| `--titles-only` | off | Fast scan — no comments fetched |
| `--max-age-days` | 365 (fetch) / 1825 (search) | Recency filter on created_utc |
| `--min-score` | 5 (fetch) / 1 (search) | Lower for search — keyword relevance matters more than score |
| `--posts-per-sub` | 20 | Posts pulled per subreddit before dedup |
| `--top-threads` | 8 | Top posts kept per subreddit after score filter |
| `--sort` | relevance (search) | Options: relevance, top, new, comments |
| `--max-per-minute` | 30 | Cross-run request budget (see below). Env: `REDDIT_FIND_MAX_PER_MIN` |

## Rate Limits & Gotchas

- **Proactive cross-run rate limiter.** Every reddit.com request passes through one shared token-bucket limiter that paces requests evenly (no bursts). Default **30 req/min** — half Reddit's ~60/min ceiling, deliberately conservative. Override per command with `--max-per-minute N` or the `REDDIT_FIND_MAX_PER_MIN` env var.
- **The budget persists across separate runs.** Recent request timestamps are stored in `~/.reddit-find/ratelimit.json` (timestamps only — no secrets). Running the tool repeatedly in a short window will *wait*, not burst, because the prior run's requests still count. This is the real defense: the original IP ban came from repeated runs, not one burst. A corrupt state file is reset automatically with a warning.
- **A blocked IP is now loud, not silent.** If Reddit's WAF blocks the IP (HTTP 403 or a block page), the tool raises a clear `IP BLOCKED:` error and exits non-zero — it no longer reports a block as a misleading "0 posts". A persistent 429 (after exponential backoff with jitter) surfaces as `RATE LIMITED:` and also exits non-zero. Remedies: wait it out, switch network/VPN, or use the RapidAPI fallback (separate feature).
- **Pre-flight + summary on stderr.** Each run prints the budget and how much is already used in the rolling window before fetching, and a usage summary (with an 80%-of-budget warning) after. All diagnostics go to stderr, so `-o` markdown and stdout piping stay clean.
- **Uses old.reddit.com JSON API** — no OAuth, no rate limit token. Reddit's unauthenticated limit is ~60 req/min. With comments enabled, each post is an additional request.
- **Titles-only first, always.** Full comment fetch on 40 posts = 80+ seconds + 40+ extra requests. Scan titles, pick winners, then deep-dive.
- **`search` mines history; `fetch` shows current.** Use `search` for specific pain phrases, `fetch` for landscape reads.
- **Windows encoding:** Tool uses UTF-8 explicitly. If redirecting stdout on Windows, use `-o file.md` instead of `>` shell redirect to avoid cp1252 issues.
- **Subreddit names are case-sensitive** in the URL but Reddit's API is tolerant. If a sub returns 0 posts, verify the exact subreddit name on reddit.com.
- **SERPER_API_KEY** only affects `discover` and the auto-discovery fallback in `fetch` (when no `-s` flags given). All three main commands work without it.

## Where to Save Output

Research outputs → `clients/gtm-client-[name]/research/` or `leadgrow-hq/archive/research/`

Feed markdown files to Claude in-session for pain point extraction, EDP mining, or content angle generation.
