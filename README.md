# reddit-find

GTM research from Reddit communities. Discovers the right subreddits, pulls high-signal threads and comments, outputs structured markdown for analysis. No API key required.

Built for B2B GTM teams who need real buyer language, not synthetic AI-generated positioning. Tool fetches — Claude analyzes.

## Install

```bash
pip install reddit-find
```

No required API keys.

**Optional:**
- `SERPER_API_KEY` — [serper.dev](https://serper.dev) for enhanced subreddit discovery (2,500 free searches/month). Without it, discovery uses Reddit's native search.

```bash
export SERPER_API_KEY="your_key"   # optional
```

## Usage

### Full pipeline

```bash
reddit-find fetch "b2b cold email" -s sales --min-score 20 -o research.md
```

Fetches threads → pulls comments → outputs structured markdown for Claude to analyze.

### Skip discovery, target known subreddits

```bash
reddit-find fetch "pipeline generation" -s sales -s b2bmarketing -o research.md
```

### Discover subreddits only

```bash
reddit-find discover "SaaS churn"
```

## Output Format

Structured markdown Claude can read directly:

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

Claude reads this and extracts: pain points, buyer language, viral moments, ICP archetypes, tool mentions, and content angles.

## Claude Code Skill

Add reddit-find as a Claude Code skill (one-liner):

```bash
curl -fsSL https://raw.githubusercontent.com/LeadGrowGTM/reddit-find/main/install-skill.sh | bash
```

## Options

```
reddit-find fetch [OPTIONS] TOPIC

  -s, --subreddit TEXT     Target subreddit (repeatable, skips discovery)
  --serper-key TEXT        SerperDev API key [env: SERPER_API_KEY] (optional)
  --posts-per-sub INT      Posts per subreddit (default: 20)
  --min-score INT          Min upvote score (default: 5)
  --top-threads INT        Top threads to fetch per sub (default: 8)
  --output, -o TEXT        Output file path
```

## How it works

1. **Discover** — Reddit native subreddit search finds communities. SerperDev (optional) adds Google-sourced signals.
2. **Fetch** — Reddit JSON API pulls hot + top posts and their best comments (no auth required)
3. **Output** — Structured markdown ready for Claude to read and analyze
4. **Analyze** — Claude in session extracts pain points, buyer language, content angles

## License

MIT — built by [LeadGrow](https://leadgrow.ai)
