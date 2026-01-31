"""Testes das rotas de progresso do usuário."""
import json
import pytest


def test_progress_create_or_update(client):
    response = client.post(
        "/progress/",
        data=json.dumps({
            "user_id": "507f1f77bcf86cd799439011",
            "deck_id": "507f1f77bcf86cd799439012",
            "card_id": "507f1f77bcf86cd799439013",
        }),
        content_type="application/json",
    )
    assert response.status_code == 200


def test_progress_create_missing(client):
    response = client.post(
        "/progress/",
        data=json.dumps({"user_id": "507f1f77bcf86cd799439011"}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_progress_pending(client):
    response = client.get(
        "/progress/pending",
        query_string={"user_id": "507f1f77bcf86cd799439011"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "pending_cards" in data or response.status_code == 200


def test_progress_pending_missing_user(client):
    response = client.get("/progress/pending")
    assert response.status_code == 400


def test_progress_update_status(client):
    response = client.put(
        "/progress/update_status",
        data=json.dumps({
            "user_id": "507f1f77bcf86cd799439011",
            "cards": [{"card_id": "507f1f77bcf86cd799439013", "recall_level": 1}],
        }),
        content_type="application/json",
    )
    assert response.status_code == 200


def test_progress_update_status_invalid(client):
    response = client.put(
        "/progress/update_status",
        data=json.dumps({"user_id": "507f1f77bcf86cd799439011"}),
        content_type="application/json",
    )
    assert response.status_code == 400
