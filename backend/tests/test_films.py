async def test_search_films(client):
    resp = await client.get("/films/search", params={"q": "fight"})
    assert resp.status_code == 200
    titles = [f["title"] for f in resp.json()]
    assert "Fight Club" in titles


async def test_get_film_detail_caches_and_returns_full_record(client):
    resp = await client.get("/films/550")
    assert resp.status_code == 200
    body = resp.json()
    assert body["tmdb_id"] == 550
    assert body["title"] == "Fight Club"
    assert body["runtime"] == 139
    assert {g["name"] for g in body["genres"]} == {"Drama", "Thriller"}
    assert any(c["name"] == "Brad Pitt" for c in body["cast"])
    assert any(c["job"] == "Director" and c["name"] == "David Fincher" for c in body["crew"])
    # US watch providers from the fake catalog.
    assert any(p["provider_name"] == "Netflix" for p in body["watch_providers"])


async def test_get_film_unknown_id_is_404(client):
    resp = await client.get("/films/999999")
    assert resp.status_code == 404


async def test_film_providers_endpoint(client):
    resp = await client.get("/films/550/providers", params={"region": "US"})
    assert resp.status_code == 200
    assert any(p["provider_name"] == "Netflix" for p in resp.json())


async def test_trending(client):
    resp = await client.get("/discover/trending")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
