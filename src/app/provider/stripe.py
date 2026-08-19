import stripe
from src.app.config import Config

stripe.api_key = Config.STRIPE_SECRET_KEY or ""
endpoint_secret = Config.STRIPE_WHSEC or ""


class Stripe:
    @staticmethod
    def is_configured():
        return bool(Config.STRIPE_SECRET_KEY and Config.PRICE_ID)

    @staticmethod
    def create_customer(email):
        if not Stripe.is_configured():
            return {"id": None}
        customer = stripe.Customer.create(email=email)
        return customer

    @staticmethod
    def create_subscription(customer_id, price_id):
        if not Stripe.is_configured():
            raise RuntimeError("Stripe is not configured")
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
        if not endpoint_secret:
            raise RuntimeError("Stripe webhook is not configured")
        event = None
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            raise e
        except stripe.error.SignatureVerificationError as e:
            raise e

        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
        else:
            print('Unhandled event type {}'.format(event['type']))

        return True
