from tests.conftest import register_user


async def test_signup_returns_token_and_user(client):
    resp = await client.post(
        "/auth/signup",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "password123",
            "display_name": "Alice",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == "alice"
    assert body["user"]["region"] == "US"  # default


async def test_signup_rejects_duplicate_username(client):
    await register_user(client, username="bob", email="bob@example.com")
    resp = await client.post(
        "/auth/signup",
        json={"username": "bob", "email": "other@example.com", "password": "password123"},
    )
    assert resp.status_code == 409


async def test_login_with_username_and_email(client):
    await register_user(client, username="carol", email="carol@example.com")

    by_username = await client.post(
        "/auth/login", json={"identifier": "carol", "password": "password123"}
    )
    assert by_username.status_code == 200
    assert by_username.json()["access_token"]

    by_email = await client.post(
        "/auth/login", json={"identifier": "carol@example.com", "password": "password123"}
    )
    assert by_email.status_code == 200


async def test_login_wrong_password_is_401(client):
    await register_user(client, username="dave")
    resp = await client.post(
        "/auth/login", json={"identifier": "dave", "password": "wrongpass1"}
    )
    assert resp.status_code == 401


async def test_me_requires_auth(client):
    assert (await client.get("/auth/me")).status_code == 401

    user = await register_user(client, username="erin")
    resp = await client.get("/auth/me", headers=user["headers"])
    assert resp.status_code == 200
    assert resp.json()["username"] == "erin"


async def test_update_profile(client):
    user = await register_user(client, username="frank")
    resp = await client.patch(
        "/auth/me",
        headers=user["headers"],
        json={"display_name": "Frank Ocean", "bio": "i watch films", "region": "gb"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["display_name"] == "Frank Ocean"
    assert body["bio"] == "i watch films"
    assert body["region"] == "GB"  # upper-cased server side


async def test_update_profile_clears_field_with_empty_string(client):
    user = await register_user(client, username="grace", display_name="Grace")
    resp = await client.patch("/auth/me", headers=user["headers"], json={"display_name": ""})
    assert resp.status_code == 200
    assert resp.json()["display_name"] is None
