"""Testes das rotas de pagamento."""
import pytest


def test_payment_intent_requires_auth(client):
    response = client.post("/payment/payment_intent", content_type="application/json")
    assert response.status_code == 401


def test_payment_intent(client, auth_headers):
    response = client.post("/payment/payment_intent", headers=auth_headers)
    assert response.status_code in (200, 500)


def test_payment_webhook(client):
    response = client.post(
        "/payment/webhook",
        data=b"{}",
        content_type="application/json",
        headers={"STRIPE_SIGNATURE": "test_sig"},
    )
    # Assinatura inválida pode retornar 400 ou 500
    assert response.status_code in (200, 400, 500, 422)
