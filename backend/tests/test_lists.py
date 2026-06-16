from tests.conftest import register_user


async def test_list_crud_and_items(client):
    user = await register_user(client, username="curator")
    h = user["headers"]

    # create
    resp = await client.post(
        "/lists",
        headers=h,
        json={"title": "Faves", "description": "my best", "is_ranked": True},
    )
    assert resp.status_code == 201
    lst = resp.json()
    list_id = lst["id"]
    assert lst["title"] == "Faves"
    assert lst["is_ranked"] is True

    # add items
    for tmdb_id in (550, 680):
        resp = await client.post(
            f"/lists/{list_id}/items", headers=h, json={"tmdb_id": tmdb_id}
        )
        assert resp.status_code == 201

    detail = await client.get(f"/lists/{list_id}")
    assert detail.status_code == 200
    assert detail.json()["item_count"] == 2

    # reorder
    resp = await client.put(
        f"/lists/{list_id}/order", headers=h, json={"tmdb_ids": [680, 550]}
    )
    assert resp.status_code == 200
    ordered = [i["film"]["tmdb_id"] for i in resp.json()["items"]]
    assert ordered == [680, 550]

    # remove an item
    resp = await client.delete(f"/lists/{list_id}/items/550", headers=h)
    assert resp.status_code == 204
    detail = await client.get(f"/lists/{list_id}")
    assert detail.json()["item_count"] == 1

    # update metadata
    resp = await client.patch(f"/lists/{list_id}", headers=h, json={"title": "Renamed"})
    assert resp.json()["title"] == "Renamed"

    # delete list
    resp = await client.delete(f"/lists/{list_id}", headers=h)
    assert resp.status_code == 204
    assert (await client.get(f"/lists/{list_id}")).status_code == 404


async def test_my_lists_listing(client):
    user = await register_user(client, username="lister")
    h = user["headers"]
    await client.post("/lists", headers=h, json={"title": "One"})
    await client.post("/lists", headers=h, json={"title": "Two"})

    resp = await client.get("/me/lists", headers=h)
    assert resp.status_code == 200
    titles = {l["title"] for l in resp.json()}
    assert {"One", "Two"} <= titles


async def test_list_likes(client):
    owner = await register_user(client, username="listowner")
    fan = await register_user(client, username="listfan")

    created = await client.post("/lists", headers=owner["headers"], json={"title": "Public"})
    list_id = created.json()["id"]

    resp = await client.post(f"/lists/{list_id}/like", headers=fan["headers"])
    assert resp.status_code == 201
    assert resp.json() == {"liked": True, "like_count": 1}

    # reflected for the fan
    resp = await client.get("/me/lists", headers=fan["headers"])
    # fan has no lists of their own; check via owner's public listing instead
    resp = await client.get(f"/users/{owner['username']}/lists", headers=fan["headers"])
    target = next(l for l in resp.json() if l["id"] == list_id)
    assert target["liked"] is True
    assert target["like_count"] == 1

    resp = await client.delete(f"/lists/{list_id}/like", headers=fan["headers"])
    assert resp.json() == {"liked": False, "like_count": 0}


async def test_list_endpoints_require_auth(client):
    assert (await client.post("/lists", json={"title": "x"})).status_code == 401
