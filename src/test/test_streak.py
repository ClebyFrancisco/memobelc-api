"""Testes das rotas de streak."""
import pytest


def test_streak_get_requires_auth(client):
    response = client.get("/streak/get")
    assert response.status_code == 401


def test_streak_get(client, auth_headers):
    response = client.get("/streak/get", headers=auth_headers)
    assert response.status_code == 200
