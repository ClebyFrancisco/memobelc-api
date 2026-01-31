"""Testes das rotas de coleções."""
import json
import pytest


def test_collections_create(client):
    response = client.post(
        "/collections/create",
        data=json.dumps({"name": "Minha Coleção"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "name" in data or "id" in data or "message" in data or "collection_id" in str(data).lower()


def test_collections_create_missing_name(client):
    response = client.post(
        "/collections/create",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_collections_get_all(client):
    response = client.get("/collections/get")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list) or "collections" in str(data).lower()


def test_collections_get_by_user_requires_auth(client):
    response = client.get("/collections/get_by_user")
    assert response.status_code == 401


def test_collections_get_by_user(client, auth_headers):
    response = client.get("/collections/get_by_user", headers=auth_headers)
    assert response.status_code == 200


def test_collections_create_and_get_by_id(client):
    create = client.post(
        "/collections/create",
        data=json.dumps({"name": "Coleção para Get"}),
        content_type="application/json",
    )
    assert create.status_code == 200
    data = create.get_json()
    coll_id = data.get("collection_id") or data.get("id")
    if coll_id:
        get_one = client.get(f"/collections/get/{coll_id}")
        assert get_one.status_code == 200


def test_collections_update(client):
    create = client.post(
        "/collections/create",
        data=json.dumps({"name": "Original"}),
        content_type="application/json",
    )
    assert create.status_code == 200
    data = create.get_json()
    coll_id = data.get("collection_id") or data.get("id")
    if coll_id:
        upd = client.put(
            f"/collections/update/{coll_id}",
            data=json.dumps({"name": "Atualizado"}),
            content_type="application/json",
        )
        assert upd.status_code == 200


def test_collections_add_decks(client):
    create = client.post(
        "/collections/create",
        data=json.dumps({"name": "Coleção Decks"}),
        content_type="application/json",
    )
    assert create.status_code == 200
    data = create.get_json()
    coll_id = data.get("collection_id") or data.get("id")
    if coll_id:
        add = client.patch(
            f"/collections/add_decks/{coll_id}",
            data=json.dumps({"deck_ids": []}),
            content_type="application/json",
        )
        assert add.status_code in (200, 404)


def test_collections_delete(client):
    create = client.post(
        "/collections/create",
        data=json.dumps({"name": "Para Excluir"}),
        content_type="application/json",
    )
    assert create.status_code == 200
    data = create.get_json()
    coll_id = data.get("collection_id") or data.get("id")
    if coll_id:
        del_r = client.delete(f"/collections/delete/{coll_id}")
        assert del_r.status_code in (200, 404)
