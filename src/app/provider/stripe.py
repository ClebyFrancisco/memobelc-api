import stripe
from src.app.config import Config

stripe.api_key=Config.STRIPE_SECRET_KEY
endpoint_secret=Config.STRIPE_WHSEC



class Stripe:
    @staticmethod
    def create_customer(email):
        customer = stripe.Customer.create(email=email)
        return customer
    
    
    @staticmethod
    def create_subscription(customer_id, price_id):

        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
        )

        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret
        }
        
    @staticmethod  
    def stripe_webhook(payload, sig_header):
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
            print(event)
        except ValueError as e:
            raise e
        except stripe.error.SignatureVerificationError as e:
            raise e


        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']

        else:
            print('Unhandled event type {}'.format(event['type']))

        return True