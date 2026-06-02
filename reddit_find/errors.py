"""Typed errors for the reddit.com request path.

These exist so the caller and CLI can tell a hard failure (IP blocked, rate
limited) apart from a genuinely empty result. They must never be swallowed and
rendered as "0 posts".
"""


class RedditBlockedError(RuntimeError):
    """Raised when Reddit's WAF has blocked this IP (HTTP 403 or block page)."""
