"""Proactive, cross-run rate limiting for reddit.com requests.

A single shared limiter paces all outbound requests so the tool can never
burst past Reddit's tolerance and ban the IP. The limiter is a token bucket
with a capacity of one: requests are spaced evenly at 60 / max_per_minute
seconds apart, never bursted. This is deliberately conservative — the goal is
to under-request, not to squeeze the rate ceiling.

The real cause of the original IP ban was repeated *runs*, not one burst, so
the limiter persists recent request timestamps to a local state file and loads
them on startup. A second run within the rolling window therefore waits for the
budget the previous run consumed. Wall-clock time is used (not monotonic) so the
state is meaningful across separate processes; the rolling window need only be
approximately right, and it errs toward under-requesting.

The state file holds nothing but request timestamps — no secrets — per the
workspace credential-safety rules.
"""

import json
import sys
import threading
import time
from pathlib import Path
from typing import Callable, List, Optional

DEFAULT_WINDOW_SECONDS = 60.0


def default_state_path() -> Path:
    """Per-user state file location: ``~/.reddit-find/ratelimit.json``."""
    return Path.home() / ".reddit-find" / "ratelimit.json"


class RateLimiter:
    """Paces requests to at most ``max_per_minute``, evenly spaced.

    ``acquire()`` blocks until a token is available, then consumes it. With a
    capacity of one token the limiter never allows a burst: each request waits
    until one interval (60 / max_per_minute seconds) after the previous one.

    When ``state_path`` is given, recent request timestamps are persisted there
    and reloaded on construction, so the budget is enforced across separate
    runs. When it is ``None`` the limiter is purely in-memory.

    ``time_fn`` and ``sleep_fn`` are injectable for testing.
    """

    def __init__(
        self,
        max_per_minute: int = 30,
        *,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
        state_path: Optional[str] = None,
        time_fn: Callable[[], float] = time.time,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_per_minute <= 0:
            raise ValueError("max_per_minute must be a positive integer")
        self.max_per_minute = max_per_minute
        self._interval = 60.0 / max_per_minute
        self._window = window_seconds
        self._state_path = Path(state_path) if state_path is not None else None
        self._time = time_fn
        self._sleep = sleep_fn
        self._lock = threading.Lock()
        self._timestamps: List[float] = self._load_state()

    def acquire(self) -> None:
        """Block until a token is available, then record its consumption."""
        with self._lock:
            now = self._time()
            self._prune(now)
            earliest_next = self._timestamps[-1] + self._interval if self._timestamps else now
            wait = max(0.0, earliest_next - now)
            consumed_at = now + wait
            self._timestamps.append(consumed_at)
            self._prune(consumed_at)
            self._save_state()
        if wait > 0:
            self._sleep(wait)

    # -- internal --------------------------------------------------------

    def _prune(self, now: float) -> None:
        cutoff = now - self._window
        self._timestamps = [t for t in self._timestamps if t > cutoff]

    def _load_state(self) -> List[float]:
        if self._state_path is None or not self._state_path.exists():
            return []
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            timestamps = [float(t) for t in data["timestamps"]]
        except (ValueError, KeyError, TypeError, OSError):
            print(
                f"reddit-find: rate-limit state file {self._state_path} was unreadable; resetting it.",
                file=sys.stderr,
            )
            return []
        cutoff = self._time() - self._window
        return [t for t in timestamps if t > cutoff]

    def _save_state(self) -> None:
        if self._state_path is None:
            return
        try:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            self._state_path.write_text(
                json.dumps({"timestamps": self._timestamps}), encoding="utf-8"
            )
        except OSError:
            # Persistence is best-effort; a write failure must not break a fetch.
            print(
                f"reddit-find: could not write rate-limit state to {self._state_path}.",
                file=sys.stderr,
            )


_shared_limiter: Optional[RateLimiter] = None


def get_limiter() -> RateLimiter:
    """Return the process-wide shared limiter, creating it on first use.

    A single instance is shared across the fetch and discover paths so every
    reddit.com request draws from one persisted budget.
    """
    global _shared_limiter
    if _shared_limiter is None:
        _shared_limiter = RateLimiter(state_path=str(default_state_path()))
    return _shared_limiter
