"""Tests that every reddit.com request routes through one shared limiter (US-003)."""

from unittest.mock import Mock, patch

from reddit_find import discover, fetch, ratelimit


def _ok_resp(text='{"data": {}}', json_data=None):
    m = Mock()
    m.status_code = 200
    m.text = text
    m.json.return_value = {"data": {}} if json_data is None else json_data
    m.raise_for_status.return_value = None
    return m


def test_get_acquires_a_token_before_each_request():
    """_get must pass through the limiter before hitting the network."""
    order = []
    limiter = Mock()
    limiter.acquire.side_effect = lambda: order.append("acquire")

    def fake_get(*a, **k):
        order.append("get")
        return _ok_resp()

    with patch.object(fetch, "get_limiter", return_value=limiter), patch.object(
        fetch.requests, "get", side_effect=fake_get
    ):
        fetch._get("https://old.reddit.com/r/x/hot.json", {})

    assert order == ["acquire", "get"], "limiter.acquire() must precede requests.get"


def test_discover_search_acquires_a_token_before_request():
    """The discover path shares the same limiter gate."""
    order = []
    limiter = Mock()
    limiter.acquire.side_effect = lambda: order.append("acquire")

    def fake_get(*a, **k):
        order.append("get")
        return _ok_resp(json_data={"data": {"children": []}})

    with patch.object(discover, "get_limiter", return_value=limiter), patch.object(
        discover.requests, "get", side_effect=fake_get
    ):
        discover._reddit_subreddit_search("b2b cold email")

    assert order == ["acquire", "get"]


def test_limiter_is_a_single_shared_instance():
    """One limiter per process — both modules get the same object."""
    ratelimit._shared_limiter = None
    first = ratelimit.get_limiter()
    second = ratelimit.get_limiter()
    assert first is second
