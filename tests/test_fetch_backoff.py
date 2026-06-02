"""Tests for exponential backoff + jitter on HTTP 429 (US-004)."""

from unittest.mock import Mock, patch

import pytest

from reddit_find import fetch
from reddit_find.errors import RedditRateLimitError


def _resp(status=200, json_data=None):
    m = Mock()
    m.status_code = status
    m.text = "" if status != 200 else '{"data": {}}'
    m.json.return_value = {} if json_data is None else json_data
    m.raise_for_status.return_value = None
    return m


def test_429_then_200_retries_once_and_succeeds():
    """A transient 429 backs off once, then the 200 succeeds."""
    seq = [_resp(status=429), _resp(status=200, json_data={"data": {"ok": True}})]
    with patch.object(fetch, "get_limiter", return_value=Mock()), patch.object(
        fetch.requests, "get", side_effect=seq
    ), patch.object(fetch.time, "sleep") as sleep:
        result = fetch._get("https://old.reddit.com/r/x/hot.json", {})

    assert result == {"data": {"ok": True}}
    assert sleep.call_count == 1
    delay = sleep.call_args.args[0]
    assert 4.0 <= delay <= 6.0, f"first backoff should be ~5s ±20%, got {delay}"


def test_persistent_429_raises_after_backoffs():
    """Unrelenting 429s exhaust retries and raise a typed error — never None."""
    with patch.object(fetch, "get_limiter", return_value=Mock()), patch.object(
        fetch.requests, "get", return_value=_resp(status=429)
    ), patch.object(fetch.time, "sleep") as sleep:
        with pytest.raises(RedditRateLimitError):
            fetch._get("https://old.reddit.com/r/x/hot.json", {})

    # default 3 retries -> three backoff sleeps, growing 5 / 15 / 45 (±20%)
    assert sleep.call_count == 3
    bases = [5, 15, 45]
    for call, base in zip(sleep.call_args_list, bases):
        delay = call.args[0]
        assert base * 0.8 <= delay <= base * 1.2, f"backoff {delay} not within ±20% of {base}"
