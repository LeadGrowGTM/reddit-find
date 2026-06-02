"""Tests for cross-run limiter state persistence (US-002)."""

import json

from reddit_find.ratelimit import RateLimiter


def _fake_clock(start=1000.0):
    """Return (now_fn, sleep_fn) sharing a mutable clock; sleeping advances it."""
    clock = [start]

    def now():
        return clock[0]

    def sleep(seconds):
        clock[0] += seconds

    return now, sleep, clock


def test_second_run_waits_for_budget_consumed_by_first_run(tmp_path):
    """A fresh limiter (new run) honors the budget the previous run used."""
    state = tmp_path / "ratelimit.json"
    now, sleep, clock = _fake_clock()

    # Run 1: one request at 30/min (2s spacing). Empty budget -> no wait.
    run1 = RateLimiter(max_per_minute=30, state_path=str(state), time_fn=now, sleep_fn=sleep)
    run1.acquire()
    assert clock[0] == 1000.0, "first request in an empty window should not wait"

    # Run 2: brand-new limiter, same state file, no wall-clock time has passed.
    run2 = RateLimiter(max_per_minute=30, state_path=str(state), time_fn=now, sleep_fn=sleep)
    run2.acquire()

    # Run 1 consumed a token at t=1000; spacing is 2s, so run 2 waits ~2s.
    assert clock[0] == 1002.0, "second run must wait for the persisted budget"


def test_state_file_holds_only_timestamps(tmp_path):
    """No secrets on disk — just request timestamps (credential-safety)."""
    state = tmp_path / "ratelimit.json"
    now, sleep, _ = _fake_clock()
    limiter = RateLimiter(max_per_minute=60, state_path=str(state), time_fn=now, sleep_fn=sleep)

    limiter.acquire()

    data = json.loads(state.read_text())
    assert set(data.keys()) == {"timestamps"}
    assert all(isinstance(t, (int, float)) for t in data["timestamps"])


def test_corrupt_state_file_resets_gracefully(tmp_path, capsys):
    """A garbage state file is reset with a warning, not a crash."""
    state = tmp_path / "ratelimit.json"
    state.write_text("not json {{{")
    now, sleep, _ = _fake_clock()

    limiter = RateLimiter(max_per_minute=60, state_path=str(state), time_fn=now, sleep_fn=sleep)
    limiter.acquire()  # must not raise

    assert "resetting" in capsys.readouterr().err.lower()


def test_old_timestamps_pruned_on_load(tmp_path):
    """Timestamps older than the window are dropped when loaded."""
    state = tmp_path / "ratelimit.json"
    state.write_text(json.dumps({"timestamps": [100.0, 200.0]}))  # ancient
    now, sleep, _ = _fake_clock(start=10_000.0)

    limiter = RateLimiter(
        max_per_minute=60,
        window_seconds=60,
        state_path=str(state),
        time_fn=now,
        sleep_fn=sleep,
    )
    limiter.acquire()

    data = json.loads(state.read_text())
    assert data["timestamps"] == [10_000.0], "ancient timestamps should be pruned"


def test_requests_in_window_counts_persisted_requests(tmp_path):
    """The window count reflects requests across runs (feeds the preflight)."""
    state = tmp_path / "ratelimit.json"
    now, sleep, _ = _fake_clock()
    limiter = RateLimiter(max_per_minute=60, state_path=str(state), time_fn=now, sleep_fn=sleep)

    limiter.acquire()
    limiter.acquire()

    assert limiter.requests_in_window() == 2


def test_tracks_requests_and_waits_for_this_run(tmp_path):
    """Per-run counters drive the end-of-run summary."""
    state = tmp_path / "ratelimit.json"
    now, sleep, _ = _fake_clock()
    limiter = RateLimiter(max_per_minute=60, state_path=str(state), time_fn=now, sleep_fn=sleep)

    limiter.acquire()  # empty budget -> no wait
    limiter.acquire()  # paced -> one wait

    assert limiter.requests_this_run == 2
    assert limiter.waited_this_run == 1
