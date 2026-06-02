"""Pre-flight note + end-of-run budget summary (US-007)."""

from reddit_find import cli as cli_mod
from reddit_find.ratelimit import RateLimiter


def _fake_clock(start=1000.0):
    clock = [start]
    return (lambda: clock[0]), (lambda s: clock.__setitem__(0, clock[0] + s))


def _limiter(max_per_minute, acquires):
    now, sleep = _fake_clock()
    limiter = RateLimiter(max_per_minute=max_per_minute, time_fn=now, sleep_fn=sleep)
    for _ in range(acquires):
        limiter.acquire()
    return limiter


def test_preflight_reports_budget_and_window_usage(capsys):
    """Before fetching: show the budget and how much is already used."""
    cli_mod._print_preflight(_limiter(30, acquires=2))
    err = capsys.readouterr().err.lower()
    assert "30" in err  # budget
    assert "2" in err    # used in window
    assert "min" in err  # per-minute budget framing


def test_run_summary_reports_run_and_window_counts(capsys):
    """After the run: requests this run, window usage, budget."""
    cli_mod._print_run_summary(_limiter(30, acquires=2))
    err = capsys.readouterr().err.lower()
    assert "2" in err
    assert "30" in err


def test_run_summary_warns_when_over_80pct_of_budget(capsys):
    """Crossing ~80% of the window budget gets a distinct warning line."""
    cli_mod._print_run_summary(_limiter(5, acquires=4))  # 4/5 = 80%
    err = capsys.readouterr().err.lower()
    assert "warning" in err
    assert "80" in err
