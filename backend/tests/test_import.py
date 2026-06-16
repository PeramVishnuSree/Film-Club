from tests.conftest import register_user

WATCHLIST_CSV = (
    "Date,Name,Year,Letterboxd URI\n"
    "2024-01-01,Fight Club,1999,https://letterboxd.com/film/fight-club/\n"
    "2024-01-02,Pulp Fiction,1994,https://letterboxd.com/film/pulp-fiction/\n"
    "2024-01-03,Nonexistent Movie,2050,https://letterboxd.com/film/nope/\n"
)

RATINGS_CSV = (
    "Date,Name,Year,Letterboxd URI,Rating\n"
    "2024-02-01,Fight Club,1999,https://letterboxd.com/film/fight-club/,4.5\n"
)

DIARY_CSV = (
    "Date,Name,Year,Letterboxd URI,Rating,Rewatch,Tags,Watched Date\n"
    "2024-03-01,Forrest Gump,1994,https://letterboxd.com/film/forrest-gump/,5,No,,2024-03-01\n"
)


async def _upload(client, headers, csv_text, filename="watchlist.csv"):
    return await client.post(
        "/me/import/letterboxd",
        headers=headers,
        files={"file": (filename, csv_text.encode("utf-8"), "text/csv")},
    )


async def test_import_watchlist(client):
    user = await register_user(client, username="importer")
    h = user["headers"]

    resp = await _upload(client, h, WATCHLIST_CSV)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["kind"] == "watchlist"
    assert body["rows"] == 3
    assert body["imported"] == 2
    assert any("Nonexistent Movie" in t for t in body["unmatched"])

    # the matched films are now on the watchlist
    wl = await client.get("/me/watchlist", headers=h)
    ids = {f["tmdb_id"] for f in wl.json()}
    assert {550, 680} <= ids


async def test_import_is_idempotent(client):
    user = await register_user(client, username="reimporter")
    h = user["headers"]

    await _upload(client, h, WATCHLIST_CSV)
    resp = await _upload(client, h, WATCHLIST_CSV)
    body = resp.json()
    # second run imports nothing new
    assert body["imported"] == 0
    assert body["skipped"] == 2


async def test_import_ratings(client):
    user = await register_user(client, username="ratingimporter")
    h = user["headers"]

    resp = await _upload(client, h, RATINGS_CSV, filename="ratings.csv")
    body = resp.json()
    assert body["kind"] == "ratings"
    assert body["imported"] == 1

    state = await client.get("/films/550/me", headers=h)
    assert state.json()["rating"] == 4.5


async def test_import_diary(client):
    user = await register_user(client, username="diaryimporter")
    h = user["headers"]

    resp = await _upload(client, h, DIARY_CSV, filename="diary.csv")
    body = resp.json()
    assert body["kind"] == "diary"
    assert body["imported"] == 1

    diary = await client.get("/me/diary", headers=h)
    assert diary.json()[0]["film_tmdb_id"] == 13


async def test_import_requires_auth(client):
    resp = await _upload(client, {}, WATCHLIST_CSV)
    assert resp.status_code == 401
