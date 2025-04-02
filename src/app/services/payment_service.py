import stripe
from werkzeug.exceptions import BadRequest, Unauthorized

from src.app.models.user_model import UserModel
from src.app.config import Config


stripe.api_key = Config.STRIPE_SECRET_KEY

class PaymentService:
    
    @staticmethod
    def create_subscription(user_id):
        user = UserModel.find_by_id(user_id)
        price_id = Config.PRICE_ID
        
        
        user = user.to_dict()
        
        if not user:
            return BadRequest(description="error: user not found!")
        
        
        subscription = stripe.Subscription.create(
        customer= user.get('customer_id'),
        items=[{"price": price_id}],
        payment_behavior="default_incomplete",
        expand=["latest_invoice.payment_intent"],
        )
        print(subscription)

        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret
        }