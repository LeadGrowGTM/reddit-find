"""Proactive rate limiting for reddit.com requests.

A single shared limiter paces all outbound requests so the tool can never
burst past Reddit's tolerance and ban the IP. The limiter is a token bucket
with a capacity of one: requests are spaced evenly at 60 / max_per_minute
seconds apart, never bursted. This is deliberately conservative — the goal is
to under-request, not to squeeze the rate ceiling.
"""

import threading
import time
from typing import Optional


class RateLimiter:
    """Paces requests to at most ``max_per_minute``, evenly spaced.

    ``acquire()`` blocks until a token is available, then consumes it. With a
    capacity of one token the limiter never allows a burst: the first call
    returns immediately, and each subsequent call waits until one interval
    (60 / max_per_minute seconds) has elapsed since the previous one.
    """

    def __init__(self, max_per_minute: int = 30) -> None:
        if max_per_minute <= 0:
            raise ValueError("max_per_minute must be a positive integer")
        self.max_per_minute = max_per_minute
        self._interval = 60.0 / max_per_minute
        self._lock = threading.Lock()
        self._next_available: Optional[float] = None  # monotonic time of next free token

    def acquire(self) -> None:
        """Block until a token is available, then consume one."""
        with self._lock:
            now = time.monotonic()
            if self._next_available is None or now >= self._next_available:
                self._next_available = now + self._interval
                return
            wait = self._next_available - now
            self._next_available += self._interval
        time.sleep(wait)


_shared_limiter: Optional[RateLimiter] = None


def get_limiter() -> RateLimiter:
    """Return the process-wide shared limiter, creating it on first use.

    A single instance is shared across the fetch and discover paths so every
    reddit.com request draws from one budget.
    """
    global _shared_limiter
    if _shared_limiter is None:
        _shared_limiter = RateLimiter()
    return _shared_limiter
