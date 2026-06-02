"""Shared test fixtures."""

import pytest

from reddit_find import ratelimit


@pytest.fixture(autouse=True)
def isolate_limiter_state(tmp_path, monkeypatch):
    """Keep the shared limiter off the real ~/.reddit-find state file.

    Points the default state path at a temp dir and resets the process-wide
    singleton around every test so runs never contaminate each other or the
    user's home directory.
    """
    monkeypatch.setattr(ratelimit, "default_state_path", lambda: tmp_path / "ratelimit.json")
    ratelimit._shared_limiter = None
    yield
    ratelimit._shared_limiter = None
