"""Password-reset and email-verification flows.

Email delivery is stubbed: instead of sending, we capture the (recipient, token)
pairs the endpoints hand to the email layer, then drive the confirm endpoints
with the captured tokens — exercising the real token signing/verification.
"""

import pytest

import app.api.auth as auth_module
from tests.conftest import register_user


@pytest.fixture
def sent_emails(monkeypatch):
    """Capture verification + reset emails the API would have sent."""
    captured: dict[str, list[tuple[str, str]]] = {"verify": [], "reset": []}

    async def fake_verify(to: str, token: str) -> None:
        captured["verify"].append((to, token))

    async def fake_reset(to: str, token: str) -> None:
        captured["reset"].append((to, token))

    monkeypatch.setattr(auth_module, "send_verification_email", fake_verify)
    monkeypatch.setattr(auth_module, "send_password_reset_email", fake_reset)
    return captured


async def test_signup_sends_verification_email(client, sent_emails):
    await register_user(client, username="newbie", email="newbie@example.com")
    assert sent_emails["verify"], "signup should trigger a verification email"
    to, token = sent_emails["verify"][0]
    assert to == "newbie@example.com"
    assert token


async def test_email_verification_flow(client, sent_emails):
    user = await register_user(client, username="verifier", email="v@example.com")

    # not verified yet
    me = await client.get("/auth/me", headers=user["headers"])
    assert me.json()["email_verified"] is False

    _, token = sent_emails["verify"][0]
    resp = await client.post("/auth/verify-email/confirm", json={"token": token})
    assert resp.status_code == 200

    me = await client.get("/auth/me", headers=user["headers"])
    assert me.json()["email_verified"] is True


async def test_verify_email_rejects_bad_token(client):
    resp = await client.post("/auth/verify-email/confirm", json={"token": "garbage"})
    assert resp.status_code == 400


async def test_resend_verification_requires_auth(client):
    assert (await client.post("/auth/verify-email/request")).status_code == 401


async def test_password_reset_flow(client, sent_emails):
    await register_user(client, username="forgetful", email="f@example.com", password="oldpass123")

    # request a reset
    resp = await client.post("/auth/password-reset/request", json={"email": "f@example.com"})
    assert resp.status_code == 200
    assert sent_emails["reset"], "reset email should be queued"
    _, token = sent_emails["reset"][0]

    # confirm with a new password
    resp = await client.post(
        "/auth/password-reset/confirm",
        json={"token": token, "new_password": "brandnew123"},
    )
    assert resp.status_code == 200

    # old password no longer works, new one does
    bad = await client.post(
        "/auth/login", json={"identifier": "forgetful", "password": "oldpass123"}
    )
    assert bad.status_code == 401
    good = await client.post(
        "/auth/login", json={"identifier": "forgetful", "password": "brandnew123"}
    )
    assert good.status_code == 200


async def test_password_reset_token_is_single_use(client, sent_emails):
    await register_user(client, username="onceonly", email="o@example.com", password="oldpass123")
    await client.post("/auth/password-reset/request", json={"email": "o@example.com"})
    _, token = sent_emails["reset"][0]

    first = await client.post(
        "/auth/password-reset/confirm",
        json={"token": token, "new_password": "firstnew123"},
    )
    assert first.status_code == 200

    # Reusing the same token after the password changed must fail.
    second = await client.post(
        "/auth/password-reset/confirm",
        json={"token": token, "new_password": "secondnew123"},
    )
    assert second.status_code == 400


async def test_password_reset_unknown_email_is_silent(client, sent_emails):
    resp = await client.post(
        "/auth/password-reset/request", json={"email": "nobody@example.com"}
    )
    # Same 200 response, but nothing was sent (no account enumeration).
    assert resp.status_code == 200
    assert sent_emails["reset"] == []
