from flask import Blueprint, jsonify, request
from src.app.middlewares.token_required import token_required
from src.app.services.payment_service import PaymentService
from src.app.provider.stripe import Stripe


class PaymentController:
    @staticmethod
    @token_required
    def create_subscription(current_user, token):
        response = PaymentService.create_subscription(current_user._id)
        return jsonify(response), 200
    
    
    @staticmethod
    def stripe_webhook():
        payload = request.data
        sig_header = request.headers['STRIPE_SIGNATURE']
        
        response = Stripe.stripe_webhook(payload, sig_header)

        return jsonify(response)

        
payment_blueprint = Blueprint("payment_blueprint", __name__)

payment_blueprint.route("/payment_intent", methods=["POST"])(PaymentController.create_subscription)
payment_blueprint.route("/webhook", methods=["POST"])(PaymentController.stripe_webhook)