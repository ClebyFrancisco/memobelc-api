from flask import Blueprint, jsonify, request
from src.app.middlewares.token_required import token_required
from src.app.provider.stripe import Stripe


class PaymentController:
    @staticmethod
    @token_required
    def create_subscription(current_user, token):
        return jsonify({
            "error": "Stripe checkout is disabled. Use /billing/checkout with Asaas.",
            "code": "stripe_disabled",
        }), 410

    @staticmethod
    def stripe_webhook():
        if not Stripe.is_configured():
            return jsonify({"error": "Stripe is disabled"}), 410
        payload = request.data
        sig_header = request.headers.get("STRIPE_SIGNATURE", "")
        try:
            response = Stripe.stripe_webhook(payload, sig_header)
            return jsonify(response), 200
        except Exception as e:
            if "SignatureVerification" in type(e).__name__ or "Signature" in type(e).__name__:
                return jsonify({"error": "Invalid signature"}), 400
            return jsonify({"error": str(e)}), 500


payment_blueprint = Blueprint("payment_blueprint", __name__)

payment_blueprint.route("/payment_intent", methods=["POST"])(PaymentController.create_subscription)
payment_blueprint.route("/webhook", methods=["POST"])(PaymentController.stripe_webhook)
