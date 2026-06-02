"""CLI surfaces block / rate-limit distinctly from empty results (US-006)."""

from click.testing import CliRunner

from reddit_find import cli as cli_mod
from reddit_find.errors import RedditBlockedError, RedditRateLimitError


def test_block_error_is_distinct_and_exits_nonzero(monkeypatch):
    """A block prints a clear message + remedy, exits non-zero — not '0 posts'."""

    def boom(*a, **k):
        raise RedditBlockedError(
            "Reddit has blocked this IP (rate-limit/WAF). Wait it out, switch "
            "networks/VPN, or use the RapidAPI fallback (separate feature)."
        )

    monkeypatch.setattr(cli_mod, "search_posts", boom)
    result = CliRunner().invoke(cli_mod.cli, ["search", "x"])

    assert result.exit_code != 0
    out = result.output.lower()
    assert "blocked" in out
    assert "0 posts" not in out and "no posts found" not in out
    assert "vpn" in out or "wait" in out  # remedy pointer present


def test_rate_limit_error_is_distinct_and_exits_nonzero(monkeypatch):
    """An exhausted-retry rate limit is surfaced, not swallowed."""

    def boom(*a, **k):
        raise RedditRateLimitError("Reddit rate-limited this IP (HTTP 429) after 3 backoff retries.")

    monkeypatch.setattr(cli_mod, "search_posts", boom)
    result = CliRunner().invoke(cli_mod.cli, ["search", "x"])

    assert result.exit_code != 0
    assert "rate" in result.output.lower()


def test_genuinely_empty_result_keeps_plain_message_and_exit_1(monkeypatch):
    """A real empty result is visibly different from a block."""
    monkeypatch.setattr(cli_mod, "search_posts", lambda **k: [])
    result = CliRunner().invoke(cli_mod.cli, ["search", "x"])

    assert result.exit_code == 1
    out = result.output.lower()
    assert "no posts found" in out
    assert "blocked" not in out
