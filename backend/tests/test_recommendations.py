from tests.conftest import register_user


async def test_recommendations_from_followee_ratings(client):
    me = await register_user(client, username="viewer")
    mentor = await register_user(client, username="mentor")

    # I follow mentor, who rates Pulp Fiction highly.
    await client.post("/users/mentor/follow", headers=me["headers"])
    await client.put("/films/680/rating", headers=mentor["headers"], json={"value": 5.0})

    resp = await client.get("/discover/recommendations", headers=me["headers"])
    assert resp.status_code == 200
    recs = resp.json()
    rec = next((r for r in recs if r["tmdb_id"] == 680), None)
    assert rec is not None, "followee's highly-rated film should be recommended"
    assert rec["reason"]  # a human-readable explanation is attached


async def test_recommendations_exclude_already_seen(client):
    me = await register_user(client, username="seen")
    mentor = await register_user(client, username="guru")

    await client.post("/users/guru/follow", headers=me["headers"])
    await client.put("/films/680/rating", headers=mentor["headers"], json={"value": 5.0})
    # I've already rated 680 myself -> it should be filtered out.
    await client.put("/films/680/rating", headers=me["headers"], json={"value": 3.0})

    resp = await client.get("/discover/recommendations", headers=me["headers"])
    assert 680 not in [r["tmdb_id"] for r in resp.json()]


async def test_recommendations_requires_auth(client):
    assert (await client.get("/discover/recommendations")).status_code == 401
