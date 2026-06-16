"""Tests for the production-hardening additions: the in-process rate limiter
and the production config guard."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.core.ratelimit import SlidingWindowLimiter, rate_limit


def test_sliding_window_blocks_after_max_hits():
    limiter = SlidingWindowLimiter(max_hits=3, window_seconds=60)
    for _ in range(3):
        limiter.check("ip-a")  # first three allowed
    with pytest.raises(Exception) as exc:
        limiter.check("ip-a")  # fourth trips it
    assert getattr(exc.value, "status_code", None) == 429


def test_sliding_window_is_per_key():
    limiter = SlidingWindowLimiter(max_hits=1, window_seconds=60)
    limiter.check("ip-a")
    limiter.check("ip-b")  # different key has its own budget
    with pytest.raises(Exception):
        limiter.check("ip-a")


async def test_login_rate_limited_when_enabled(client, monkeypatch):
    """With limiting on, the 11th login attempt in the window returns 429."""
    from app.config import settings

    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    last = None
    for _ in range(12):
        last = await client.post(
            "/auth/login", json={"identifier": "nobody", "password": "x"}
        )
    assert last.status_code == 429
    assert "retry-after" in {k.lower() for k in last.headers}


def test_dependency_skips_when_disabled():
    # When disabled the dependency factory still builds; the guard is checked at
    # call time against settings (covered end-to-end by the suite running with
    # rate_limit_enabled=False).
    dep = rate_limit(max_hits=1, window_seconds=1, scope="t")
    assert callable(dep)


def test_production_guard_rejects_default_secret():
    s = Settings(environment="production", secret_key="change-me", tmdb_api_key="x")
    with pytest.raises(RuntimeError) as exc:
        s.validate_for_production()
    assert "SECRET_KEY" in str(exc.value)


def test_production_guard_requires_tmdb_credential():
    s = Settings(
        environment="production",
        secret_key="a" * 40,
        tmdb_api_key="",
        tmdb_access_token="",
    )
    with pytest.raises(RuntimeError) as exc:
        s.validate_for_production()
    assert "TMDB" in str(exc.value)


def test_production_guard_passes_with_good_config():
    s = Settings(
        environment="production",
        secret_key="a" * 40,
        tmdb_access_token="token",
    )
    s.validate_for_production()  # should not raise


def test_development_guard_is_lenient():
    s = Settings(environment="development", secret_key="change-me")
    s.validate_for_production()  # no-op outside production
