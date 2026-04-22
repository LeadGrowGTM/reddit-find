# reddit-find

GTM research from Reddit communities. Discovers the right subreddits, pulls high-signal threads, and extracts structured intelligence — pain points, buyer language, viral moments, and content angles.

Built for B2B GTM teams who need real buyer language, not synthetic AI-generated positioning.

## Install

```bash
pip install reddit-find
```

**Required API keys:**
- `SERPER_API_KEY` — [serper.dev](https://serper.dev) for subreddit discovery (2,500 free searches/month)
- `ANTHROPIC_API_KEY` — for GTM analysis (uses Claude Haiku, ~$0.002-0.005/run)

```bash
export SERPER_API_KEY="your_key"
export ANTHROPIC_API_KEY="your_key"
```

## Usage

### Full pipeline

```bash
reddit-find fetch "b2b cold email pain points" -o research.md
```

Discovers subreddits → fetches hot + top threads → pulls comments → analyzes with Claude → saves report.

### Skip discovery, target known subreddits

```bash
reddit-find fetch "pipeline generation" -s sales -s b2bmarketing -o research.md
```

### Discover subreddits only

```bash
reddit-find discover "SaaS churn"
```

## Output

Structured markdown report with:

- **Pain Points** — verbatim quotes with upvote scores
- **Buyer Language** — exact phrases for cold email subject lines and hooks
- **Viral Moments** — high-engagement threads with "why it hit" analysis
- **ICP Archetypes** — role, situation, what they're trying to solve
- **Tool & Competitor Mentions** — with sentiment
- **Content Angles** — 5 specific post ideas from actual thread language

## Claude Code Skill

Add reddit-find as a Claude Code skill (one-liner):

```bash
curl -fsSL https://raw.githubusercontent.com/LeadGrowGTM/reddit-find/main/install-skill.sh | bash
```

Once installed, Claude can run reddit-find research inline during any session.

## Options

```
reddit-find fetch [OPTIONS] TOPIC

  -s, --subreddit TEXT     Target subreddit (repeatable, skips discovery)
  --serper-key TEXT        SerperDev API key [env: SERPER_API_KEY]
  --anthropic-key TEXT     Anthropic API key [env: ANTHROPIC_API_KEY]
  --posts-per-sub INT      Posts per subreddit (default: 20)
  --min-score INT          Min upvote score (default: 5)
  --top-threads INT        Top threads to analyze per sub (default: 8)
  --output, -o TEXT        Output file path
  --model TEXT             Claude model (default: claude-haiku-4-5-20251001)
```

## How it works

1. **Discover** — SerperDev Google searches find subreddits where your ICP actually talks about the problem
2. **Fetch** — Reddit JSON API pulls hot + top posts and their best comments (no auth required)
3. **Analyze** — Claude extracts structured GTM intel from the raw threads
4. **Report** — Saves a ready-to-use research doc

## License

MIT — built by [LeadGrow](https://leadgrow.ai)
