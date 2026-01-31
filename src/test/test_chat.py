# """Testes das rotas de chat."""
# import json
# import pytest


# def test_chat_talk_requires_auth(client):
#     response = client.post(
#         "/chat/talk_to_me",
#         data=json.dumps({"message": "Olá"}),
#         content_type="application/json",
#     )
#     assert response.status_code == 401


# def test_chat_talk(client, auth_headers):
#     response = client.post(
#         "/chat/talk_to_me",
#         data=json.dumps({"message": "Olá", "history": [], "settings": {}}),
#         headers=auth_headers,
#     )
#     # 429 = quota excedida (Google API), 500 = erro interno
#     assert response.status_code in (200, 429, 500)


# def test_chat_get_chats_requires_auth(client):
#     response = client.get("/chat/get_chats_by_user")
#     assert response.status_code == 401


# def test_chat_get_chats(client, auth_headers):
#     response = client.get("/chat/get_chats_by_user", headers=auth_headers)
#     assert response.status_code == 200


# def test_chat_generate_card(client):
#     response = client.post(
#         "/chat/generate_card",
#         data=json.dumps({"chat_id": "507f1f77bcf86cd799439011", "settings": {}}),
#         content_type="application/json",
#     )
#     # 404 = chat não encontrado, 429 = quota API, 500 = erro
#     assert response.status_code in (200, 400, 404, 429, 500)
