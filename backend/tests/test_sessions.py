"""Session-revocation tests: token_version bumps invalidate old access tokens
on password reset and on explicit log-out-everywhere."""

from __future__ import annotations

from sqlalchemy import select

from app.core.security import create_password_reset_token
from app.models import User
from tests.conftest import register_user


async def test_logout_all_revokes_existing_token(client):
    reg = await register_user(client, username="alice")
    headers = reg["headers"]

    # Token works before logout-all.
    assert (await client.get("/auth/me", headers=headers)).status_code == 200

    # Revoke every session.
    resp = await client.post("/auth/logout-all", headers=headers)
    assert resp.status_code == 200

    # The same (now stale) token is rejected.
    assert (await client.get("/auth/me", headers=headers)).status_code == 401


async def test_password_reset_revokes_existing_sessions(client, session):
    reg = await register_user(client, username="bob", password="password123")
    headers = reg["headers"]
    assert (await client.get("/auth/me", headers=headers)).status_code == 200

    # Mint a valid reset token bound to the current password hash.
    user = (
        await session.execute(select(User).where(User.username == "bob"))
    ).scalar_one()
    token = create_password_reset_token(user.id, user.hashed_password)

    resp = await client.post(
        "/auth/password-reset/confirm",
        json={"token": token, "new_password": "brand-new-pass"},
    )
    assert resp.status_code == 200

    # Old access token from before the reset is now invalid.
    assert (await client.get("/auth/me", headers=headers)).status_code == 401

    # The new password works and yields a fresh, valid token.
    login = await client.post(
        "/auth/login", json={"identifier": "bob", "password": "brand-new-pass"}
    )
    assert login.status_code == 200
    new_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (await client.get("/auth/me", headers=new_headers)).status_code == 200


async def test_fresh_login_after_logout_all_works(client):
    reg = await register_user(client, username="carol", password="password123")
    await client.post("/auth/logout-all", headers=reg["headers"])
    # A new login mints a token at the bumped version, which is accepted.
    login = await client.post(
        "/auth/login", json={"identifier": "carol", "password": "password123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (await client.get("/auth/me", headers=headers)).status_code == 200
