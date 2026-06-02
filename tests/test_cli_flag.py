"""--max-per-minute flag and REDDIT_FIND_MAX_PER_MIN env var (US-008)."""

from click.testing import CliRunner

from reddit_find import cli as cli_mod


def test_flag_sets_the_budget(monkeypatch):
    """--max-per-minute overrides the default 30 budget."""
    monkeypatch.setattr(cli_mod, "search_posts", lambda **k: [])
    result = CliRunner().invoke(cli_mod.cli, ["search", "x", "--max-per-minute", "20"])
    assert "20 req/min" in result.output


def test_env_var_sets_the_budget(monkeypatch):
    """REDDIT_FIND_MAX_PER_MIN provides the default when the flag is absent."""
    monkeypatch.setenv("REDDIT_FIND_MAX_PER_MIN", "17")
    monkeypatch.setattr(cli_mod, "search_posts", lambda **k: [])
    result = CliRunner().invoke(cli_mod.cli, ["search", "x"])
    assert "17 req/min" in result.output


def test_default_budget_is_30(monkeypatch):
    """Absent flag and env var, the conservative 30/min default holds."""
    monkeypatch.delenv("REDDIT_FIND_MAX_PER_MIN", raising=False)
    monkeypatch.setattr(cli_mod, "search_posts", lambda **k: [])
    result = CliRunner().invoke(cli_mod.cli, ["search", "x"])
    assert "30 req/min" in result.output


def test_preflight_and_summary_fire_around_a_real_run(monkeypatch):
    """End-to-end: pre-flight before, summary after a command that makes a request."""
    from reddit_find import ratelimit

    def fake_search(**k):
        ratelimit.get_limiter().acquire()  # simulate one outbound request
        return []

    monkeypatch.setattr(cli_mod, "search_posts", fake_search)
    result = CliRunner().invoke(cli_mod.cli, ["search", "x", "--max-per-minute", "60"])

    assert "60 req/min" in result.output           # pre-flight printed
    assert "summary" in result.output.lower()       # end-of-run summary printed
