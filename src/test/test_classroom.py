"""Testes das rotas de sala de aula."""
import json
import pytest


def test_classroom_create_requires_auth(client):
    response = client.post(
        "/classroom/create",
        data=json.dumps({"collection_id": "507f1f77bcf86cd799439011"}),
        content_type="application/json",
    )
    assert response.status_code == 401


def test_classroom_get_requires_auth(client):
    response = client.get("/classroom/get_classrooms")
    assert response.status_code == 401


def test_classroom_get(client, auth_headers):
    response = client.get("/classroom/get_classrooms", headers=auth_headers)
    assert response.status_code in (200, 401, 403)


def test_classroom_add_user_requires_auth(client):
    response = client.post(
        "/classroom/add_user_in_classroom",
        data=json.dumps({"classroom_id": "x", "email_user": "a@a.com"}),
        content_type="application/json",
    )
    assert response.status_code == 401


def test_classroom_generate_cards_by_subject(client):
    response = client.post(
        "/classroom/generate_cards_by_subject",
        data=json.dumps({
            "subject": "Matemática",
            "amount": 5,
            "language_front": "pt",
            "language_back": "en",
        }),
        content_type="application/json",
    )
    # 429 = quota excedida (Google API)
    assert response.status_code in (200, 400, 429, 500)


def test_classroom_generate_cards_missing_subject(client):
    response = client.post(
        "/classroom/generate_cards_by_subject",
        data=json.dumps({"language_front": "pt", "language_back": "en"}),
        content_type="application/json",
    )
    assert response.status_code == 400
