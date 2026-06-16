"""Shared pytest fixtures.

Tests run against a real PostgreSQL database (default: `filmclub_test`), because
the codebase relies on Postgres-only features — `pg_insert` upserts in the film
cache and JSONB columns on interactions/notifications — that SQLite cannot model.
Each test gets a freshly created schema for full isolation.

Point the suite at a different database with the TEST_DATABASE_URL env var.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Importing the models package populates Base.metadata with every table.
import app.models  # noqa: F401
from app.api.deps import get_tmdb
from app.core.security import create_access_token
from app.db import Base, get_session
from app.main import app
from tests.fake_tmdb import FakeTMDB

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://filmclub:filmclub@localhost:5432/filmclub_test",
)


@pytest_asyncio.fixture
async def engine():
    # Function-scoped with NullPool: each test owns its own event loop, so a
    # pooled connection created in one loop must never leak into another (that
    # triggers asyncpg's "another operation is in progress").
    eng = create_async_engine(TEST_DATABASE_URL, future=True, poolclass=NullPool)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_sessionmaker(engine) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    # Fresh schema per test keeps cases independent.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield maker
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session(db_sessionmaker) -> AsyncGenerator[AsyncSession, None]:
    """A standalone session for arranging fixtures and asserting on db state."""
    async with db_sessionmaker() as s:
        yield s


@pytest_asyncio.fixture
async def client(db_sessionmaker) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client wired to the app with the test DB and a fake TMDB client."""

    async def _get_session() -> AsyncGenerator[AsyncSession, None]:
        async with db_sessionmaker() as s:
            yield s

    fake = FakeTMDB()

    app.dependency_overrides[get_session] = _get_session
    app.dependency_overrides[get_tmdb] = lambda: fake

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------- helpers


async def register_user(
    client: AsyncClient,
    username: str = "alice",
    email: str | None = None,
    password: str = "password123",
    display_name: str | None = None,
) -> dict:
    """Create a user via the API and return {token, headers, user, ...}."""
    email = email or f"{username}@example.com"
    resp = await client.post(
        "/auth/signup",
        json={
            "username": username,
            "email": email,
            "password": password,
            "display_name": display_name,
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return {
        "token": body["access_token"],
        "headers": {"Authorization": f"Bearer {body['access_token']}"},
        "user": body["user"],
        "username": username,
        "password": password,
    }


@pytest.fixture
def auth_token():
    """Mint a bearer token for an arbitrary user id without hitting the API."""

    def _make(user_id: int) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_access_token(user_id)}"}

    return _make
