"""Tests for the proactive rate limiter (US-001)."""

import threading
import time

import pytest

from reddit_find.ratelimit import RateLimiter


def test_acquire_paces_rapid_calls():
    """5 rapid acquires at 60/min are paced to ~1/sec — no bursting.

    First token is immediate; the next four each wait ~1s, so five calls
    take ~4s total. This is the core guardrail: requests never burst.
    """
    limiter = RateLimiter(max_per_minute=60)

    start = time.monotonic()
    for _ in range(5):
        limiter.acquire()
    elapsed = time.monotonic() - start

    assert elapsed >= 3.6, f"expected ~4s of pacing, got {elapsed:.2f}s (bursting)"
    assert elapsed < 6.0, f"pacing too slow: {elapsed:.2f}s"


def test_default_budget_is_30():
    """Default budget is the conservative 30/min (half Reddit's ceiling)."""
    assert RateLimiter().max_per_minute == 30


@pytest.mark.parametrize("bad", [0, -1, -30])
def test_rejects_nonpositive_budget(bad):
    """A non-positive budget is a configuration error, not a silent no-op."""
    with pytest.raises(ValueError):
        RateLimiter(max_per_minute=bad)


def test_concurrent_acquire_does_not_crash_and_still_paces():
    """Threads sharing one limiter don't crash and the budget still holds.

    Single-threaded is the real usage, but the limiter must not corrupt its
    state or burst when touched from more than one thread.
    """
    limiter = RateLimiter(max_per_minute=60)

    start = time.monotonic()
    threads = [threading.Thread(target=limiter.acquire) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.monotonic() - start

    # 4 acquires: 1 immediate + 3 paced ~1s each -> ~3s, never instant.
    assert elapsed >= 2.6, f"concurrent acquires bursted: {elapsed:.2f}s"
