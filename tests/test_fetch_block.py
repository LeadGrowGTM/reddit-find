"""Tests for 403 / WAF block detection in the fetch path (US-005)."""

from unittest.mock import Mock, patch

import pytest

from reddit_find import fetch
from reddit_find.errors import RedditBlockedError


def _resp(status=200, text="", json_data=None):
    """Build a fake requests.Response good enough for _get."""
    m = Mock()
    m.status_code = status
    m.text = text
    m.json.return_value = {} if json_data is None else json_data
    m.raise_for_status.return_value = None
    return m


def test_403_raises_blocked():
    """A 403 is an IP block — raise loudly, never return None/0-posts."""
    with patch.object(fetch.requests, "get", return_value=_resp(status=403, text="Forbidden")):
        with pytest.raises(RedditBlockedError):
            fetch._get("https://old.reddit.com/r/x/hot.json", {})


def test_block_page_body_raises():
    """A 200 whose body is Reddit's WAF block page is still a block."""
    body = "<html><head><title>Blocked</title></head>you've been blocked by network security</html>"
    with patch.object(fetch.requests, "get", return_value=_resp(status=200, text=body)):
        with pytest.raises(RedditBlockedError):
            fetch._get("https://old.reddit.com/r/x/hot.json", {})


def test_normal_json_returns_data_not_a_false_block():
    """A genuine JSON response must NOT be misread as a block."""
    with patch.object(
        fetch.requests,
        "get",
        return_value=_resp(status=200, text='{"data": {"children": []}}', json_data={"data": {"children": []}}),
    ):
        assert fetch._get("https://old.reddit.com/r/x/hot.json", {}) == {"data": {"children": []}}
