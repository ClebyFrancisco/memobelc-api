from src.app.config import Config
from src.app.models.user_model import UserModel
from src.app.provider.stripe import Stripe


class PaymentService:
    @staticmethod
    def create_subscription(user_id):
        if not Stripe.is_configured():
            return {
                "error": "Stripe checkout is disabled. Use /billing/checkout.",
                "code": "stripe_disabled",
            }
        import stripe
        stripe.api_key = Config.STRIPE_SECRET_KEY
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"error": "user not found"}
        user = user.to_dict()
        subscription = stripe.Subscription.create(
            customer=user.get("customer_id"),
            items=[{"price": Config.PRICE_ID}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
        )
        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret
        }