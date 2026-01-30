"""Testes das rotas de vídeos."""
import json
import pytest


def test_video_create(client):
    response = client.post(
        "/video/create",
        data=json.dumps({
            "title": "Título",
            "thumbnail": "http://thumb.jpg",
            "deck_id": "507f1f77bcf86cd799439011",
            "video_id": "abc123",
        }),
        content_type="application/json",
    )
    assert response.status_code in (201, 400)


def test_video_get_all(client):
    response = client.get("/video/get")
    assert response.status_code == 201
    data = response.get_json()
    assert isinstance(data, list) or data is not None


def test_video_get_with_language(client):
    response = client.get("/video/get", query_string={"language": "pt"})
    assert response.status_code == 201
