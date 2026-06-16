from tests.conftest import register_user


async def test_user_search(client):
    await register_user(client, username="searchme", display_name="Find Me")
    seeker = await register_user(client, username="seeker")

    resp = await client.get("/users/search", params={"q": "find"}, headers=seeker["headers"])
    assert resp.status_code == 200
    assert "searchme" in [u["username"] for u in resp.json()]


async def test_profile_and_follow_flow(client):
    alice = await register_user(client, username="alice")
    bob = await register_user(client, username="bob")

    # alice follows bob
    resp = await client.post("/users/bob/follow", headers=alice["headers"])
    assert resp.status_code == 201
    assert resp.json() == {"following": True}

    # idempotent
    resp = await client.post("/users/bob/follow", headers=alice["headers"])
    assert resp.status_code == 201

    # bob's profile reflects a follower, and alice sees is_following
    profile = await client.get("/users/bob", headers=alice["headers"])
    body = profile.json()
    assert body["stats"]["followers"] == 1
    assert body["is_following"] is True
    assert body["is_self"] is False

    # bob's followers / alice's following lists
    followers = await client.get("/users/bob/followers")
    assert "alice" in [u["username"] for u in followers.json()]
    following = await client.get("/users/alice/following")
    assert "bob" in [u["username"] for u in following.json()]

    # unfollow
    resp = await client.delete("/users/bob/follow", headers=alice["headers"])
    assert resp.status_code == 204
    profile = await client.get("/users/bob", headers=alice["headers"])
    assert profile.json()["stats"]["followers"] == 0


async def test_cannot_follow_self(client):
    user = await register_user(client, username="lonely")
    resp = await client.post("/users/lonely/follow", headers=user["headers"])
    assert resp.status_code == 400


async def test_follow_unknown_user_is_404(client):
    user = await register_user(client, username="present")
    resp = await client.post("/users/nobody/follow", headers=user["headers"])
    assert resp.status_code == 404


async def test_follow_generates_notification(client):
    alice = await register_user(client, username="anna")
    bob = await register_user(client, username="ben")

    await client.post("/users/ben/follow", headers=alice["headers"])

    # ben has an unread follow notification
    count = await client.get("/me/notifications/unread_count", headers=bob["headers"])
    assert count.json()["unread"] == 1

    notes = await client.get("/me/notifications", headers=bob["headers"])
    assert notes.status_code == 200
    note = notes.json()[0]
    assert note["type"] == "follow"
    assert note["actor"]["username"] == "anna"
    assert note["read"] is False

    # mark all read
    resp = await client.post("/me/notifications/read", headers=bob["headers"])
    assert resp.status_code == 204
    count = await client.get("/me/notifications/unread_count", headers=bob["headers"])
    assert count.json()["unread"] == 0


async def test_no_self_notification_on_like(client):
    """Liking your own review must not create a notification."""
    user = await register_user(client, username="selfliker")
    h = user["headers"]
    review = await client.post("/films/550/reviews", headers=h, json={"body": "mine"})
    await client.post(f"/reviews/{review.json()['id']}/like", headers=h)

    count = await client.get("/me/notifications/unread_count", headers=h)
    assert count.json()["unread"] == 0


async def test_feed_shows_followee_activity(client):
    alice = await register_user(client, username="aria")
    bob = await register_user(client, username="bobby")

    await client.post("/users/bobby/follow", headers=alice["headers"])
    # bob rates a film -> records an interaction
    await client.put("/films/550/rating", headers=bob["headers"], json={"value": 4.0})

    feed = await client.get("/me/feed", headers=alice["headers"])
    assert feed.status_code == 200
    assert any(item["actor"]["username"] == "bobby" for item in feed.json())
