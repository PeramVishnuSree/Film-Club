from tests.conftest import register_user


async def test_rating_lifecycle_and_film_state(client):
    user = await register_user(client, username="rater")
    h = user["headers"]

    # set
    resp = await client.put("/films/550/rating", headers=h, json={"value": 4.5})
    assert resp.status_code == 200
    assert resp.json()["value"] == 4.5

    # update (idempotent overwrite, not a duplicate)
    resp = await client.put("/films/550/rating", headers=h, json={"value": 5.0})
    assert resp.status_code == 200

    state = await client.get("/films/550/me", headers=h)
    assert state.json()["rating"] == 5.0

    # delete
    resp = await client.delete("/films/550/rating", headers=h)
    assert resp.status_code == 204
    state = await client.get("/films/550/me", headers=h)
    assert state.json()["rating"] is None


async def test_rating_rejects_non_half_step(client):
    user = await register_user(client, username="picky")
    resp = await client.put("/films/550/rating", headers=user["headers"], json={"value": 3.3})
    assert resp.status_code == 422


async def test_watchlist_add_remove(client):
    user = await register_user(client, username="watcher")
    h = user["headers"]

    resp = await client.post("/films/680/watchlist", headers=h)
    assert resp.status_code == 201
    assert resp.json()["watchlisted"] is True

    wl = await client.get("/me/watchlist", headers=h)
    assert resp.status_code == 201
    assert 680 in [f["tmdb_id"] for f in wl.json()]

    state = await client.get("/films/680/me", headers=h)
    assert state.json()["watchlisted"] is True

    resp = await client.delete("/films/680/watchlist", headers=h)
    assert resp.status_code == 204
    wl = await client.get("/me/watchlist", headers=h)
    assert 680 not in [f["tmdb_id"] for f in wl.json()]


async def test_diary_entry_and_state(client):
    user = await register_user(client, username="diarist")
    h = user["headers"]

    resp = await client.post(
        "/films/13/diary",
        headers=h,
        json={"watched_on": "2024-01-02", "rating_value": 4.0, "liked": True, "note": "great"},
    )
    assert resp.status_code == 201
    entry = resp.json()
    assert entry["film_tmdb_id"] == 13
    assert entry["liked"] is True

    diary = await client.get("/me/diary", headers=h)
    assert len(diary.json()) == 1

    state = await client.get("/films/13/me", headers=h)
    assert state.json()["watched"] is True

    # delete the entry
    resp = await client.delete(f"/diary/{entry['id']}", headers=h)
    assert resp.status_code == 204
    diary = await client.get("/me/diary", headers=h)
    assert diary.json() == []


async def test_protected_endpoints_require_auth(client):
    assert (await client.put("/films/550/rating", json={"value": 4.0})).status_code == 401
    assert (await client.post("/films/550/watchlist")).status_code == 401
    assert (await client.get("/me/diary")).status_code == 401


async def test_reviews_create_list_and_like(client):
    author = await register_user(client, username="author")
    liker = await register_user(client, username="liker")

    resp = await client.post(
        "/films/550/reviews",
        headers=author["headers"],
        json={"body": "A masterpiece.", "contains_spoilers": False},
    )
    assert resp.status_code == 201
    review_id = resp.json()["id"]

    # public listing, logged out
    resp = await client.get("/films/550/reviews")
    assert resp.status_code == 200
    assert resp.json()[0]["body"] == "A masterpiece."
    assert resp.json()[0]["like_count"] == 0

    # like it as another user
    resp = await client.post(f"/reviews/{review_id}/like", headers=liker["headers"])
    assert resp.status_code == 201
    assert resp.json() == {"liked": True, "like_count": 1}

    # liking again is idempotent
    resp = await client.post(f"/reviews/{review_id}/like", headers=liker["headers"])
    assert resp.json()["like_count"] == 1

    # the liker sees liked=True
    resp = await client.get("/films/550/reviews", headers=liker["headers"])
    assert resp.json()[0]["liked"] is True
    assert resp.json()[0]["like_count"] == 1

    # unlike
    resp = await client.delete(f"/reviews/{review_id}/like", headers=liker["headers"])
    assert resp.json() == {"liked": False, "like_count": 0}


async def test_like_missing_review_is_404(client):
    user = await register_user(client, username="ghost")
    resp = await client.post("/reviews/123456/like", headers=user["headers"])
    assert resp.status_code == 404
