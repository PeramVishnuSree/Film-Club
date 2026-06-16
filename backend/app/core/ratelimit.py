"""A small, dependency-free, in-process rate limiter.

Used to blunt brute-force and abuse on the auth endpoints (login, signup,
password-reset, email-verify) without pulling in Redis or a third-party lib.

Limitation: state lives in this process's memory, so with multiple workers /
replicas each instance enforces the limit independently. For a single-instance
deployment (the default docker-compose stack) it is effective; behind a load
balancer with N instances the effective limit is roughly N×. For strict global
limits, front the app with a reverse proxy / WAF or swap this for a Redis-backed
limiter.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.config import settings


class SlidingWindowLimiter:
    def __init__(self, max_hits: int, window_seconds: float) -> None:
        self.max_hits = max_hits
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        bucket = self._hits[key]
        cutoff = now - self.window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.max_hits:
            retry = int(self.window - (now - bucket[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down and try again shortly.",
                headers={"Retry-After": str(max(retry, 1))},
            )
        bucket.append(now)
        # Opportunistic cleanup so idle keys don't accumulate forever.
        if len(self._hits) > 10_000:
            for k in [k for k, b in self._hits.items() if not b]:
                self._hits.pop(k, None)


def _client_ip(request: Request) -> str:
    # Honour the first hop of X-Forwarded-For when present (set by a trusted
    # reverse proxy); fall back to the direct peer.
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(max_hits: int, window_seconds: float, scope: str):
    """Build a FastAPI dependency that limits `max_hits` per `window_seconds`
    per client IP, namespaced by `scope` so different endpoints don't share a
    budget."""
    limiter = SlidingWindowLimiter(max_hits, window_seconds)

    async def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        limiter.check(f"{scope}:{_client_ip(request)}")

    return dependency
