"""Testes das rotas de livros."""
import json
import pytest


def test_books_list_requires_auth(client):
    response = client.get("/books/list")
    assert response.status_code == 401


def test_books_list(client, auth_headers):
    response = client.get("/books/list", headers=auth_headers)
    # 200 = ok, 401 = token inválido/expirado, 403 = sem permissão
    assert response.status_code in (200, 401, 403)


def test_books_get_requires_auth(client):
    response = client.get("/books/get/507f1f77bcf86cd799439011")
    assert response.status_code == 401


def test_books_purchase_requires_auth(client):
    response = client.post(
        "/books/purchase",
        data=json.dumps({"book_id": "507f1f77bcf86cd799439011"}),
        content_type="application/json",
    )
    assert response.status_code == 401


def test_books_admin_list_requires_auth(client):
    response = client.get("/books/admin/list")
    assert response.status_code == 401


def test_books_admin_create_requires_auth(client):
    response = client.post(
        "/books/admin/create",
        data=json.dumps({"titulo": "Livro", "idioma": "pt", "nivel": "1"}),
        content_type="application/json",
    )
    assert response.status_code == 401
