from tests.conftest import register_user


async def test_stats_reflect_diary_and_ratings(client):
    user = await register_user(client, username="statto")
    h = user["headers"]

    # Two diary entries in 2024, ratings, and a review.
    await client.post(
        "/films/550/diary",
        headers=h,
        json={"watched_on": "2024-03-01", "rating_value": 4.5},
    )
    await client.post(
        "/films/680/diary",
        headers=h,
        json={"watched_on": "2024-07-15", "rating_value": 5.0},
    )
    await client.put("/films/550/rating", headers=h, json={"value": 4.5})
    await client.post("/films/550/reviews", headers=h, json={"body": "loved it"})

    resp = await client.get("/me/stats", headers=h, params={"year": 2024})
    assert resp.status_code == 200
    body = resp.json()

    lifetime = body["lifetime"]
    assert lifetime["films_logged"] == 2
    assert lifetime["entries"] == 2
    assert lifetime["ratings"] == 1
    assert lifetime["reviews"] == 1
    assert len(lifetime["rating_distribution"]) == 10  # 0.5 .. 5.0 buckets

    year = body["year"]
    assert year["year"] == 2024
    assert year["entries"] == 2
    assert year["distinct_films"] == 2
    # Fight Club 139m + Pulp Fiction 154m = 293m ≈ 4.88h
    assert 4.5 < year["hours"] < 5.5
    assert 2024 in body["available_years"]


async def test_stats_requires_auth(client):
    assert (await client.get("/me/stats")).status_code == 401


async def test_stats_empty_user(client):
    user = await register_user(client, username="fresh")
    resp = await client.get("/me/stats", headers=user["headers"])
    assert resp.status_code == 200
    assert resp.json()["lifetime"]["films_logged"] == 0
