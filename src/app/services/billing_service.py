"""Checkout, webhooks, subscription lifecycle and admin billing operations."""

from datetime import datetime, timezone, timedelta

from flask import current_app
from flask_mail import Message
from src.app import mail
from src.app.config import Config
from src.app.models.billing_support_model import AuditLogModel, ExternalSaleModel, WebhookEventModel
from src.app.models.book_bundle_model import BookBundleModel
from src.app.models.book_model import BookModel
from src.app.models.coupon_model import CouponModel
from src.app.models.entitlement_model import EntitlementModel
from src.app.models.payment_model import PaymentModel
from src.app.models.plan_model import PlanModel
from src.app.models.subscription_model import SubscriptionModel
from src.app.models.user_model import UserModel
from src.app.provider.asaas import Asaas, AsaasError
from src.app.provider.google_play import GooglePlay, GooglePlayError
from src.app.services.coupon_service import CouponService
from src.app.services.entitlement_service import EntitlementService
from src.app.utils.billing_utils import (
    ACCESS_STATUSES,
    asaas_discount_payload,
    apply_discount,
    compute_grace_until,
    cycle_timedelta,
    invoice_description,
    parse_datetime,
    product_snapshot,
    utcnow,
)


ACTIVE_BLOCKING_STATUSES = list(ACCESS_STATUSES) + ["pending", "overdue", "suspended"]


def _digits_only(value):
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _normalize_cpf_cnpj(value):
    digits = _digits_only(value)
    if len(digits) in (11, 14):
        return digits
    return None


def _asaas_error_message(exc):
    payload = exc.payload if isinstance(getattr(exc, "payload", None), dict) else {}
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict) and first.get("description"):
            return first["description"]
    return str(exc)


class BillingService:
    @staticmethod
    def _ensure_asaas_customer(user, cpf_cnpj=None):
        if user.asaas_customer_id:
            if cpf_cnpj:
                Asaas.update_customer(user.asaas_customer_id, {
                    "name": user.name or user.email,
                    "email": user.email,
                    "cpfCnpj": cpf_cnpj,
                })
                UserModel.set_cpf_cnpj(user._id, cpf_cnpj)
                user.cpf_cnpj = cpf_cnpj
            return user.asaas_customer_id
        created = Asaas.create_customer(
            user.name,
            user.email,
            external_reference=str(user._id),
            cpf_cnpj=cpf_cnpj,
        )
        customer_id = created.get("id")
        UserModel.set_asaas_customer_id(user._id, customer_id)
        if cpf_cnpj:
            UserModel.set_cpf_cnpj(user._id, cpf_cnpj)
            user.cpf_cnpj = cpf_cnpj
        user.asaas_customer_id = customer_id
        return customer_id

    @staticmethod
    def _blocking_subscription(user_id):
        for item in SubscriptionModel.list_for_user(user_id):
            if item.get("status") in ACTIVE_BLOCKING_STATUSES:
                return item
        return None

    @staticmethod
    def _product(product_type, product_id):
        if product_type == "plan":
            return PlanModel.get_by_id(product_id)
        if product_type == "book":
            return BookModel.get_by_id(product_id)
        if product_type == "bundle":
            return BookBundleModel.get_by_id(product_id)
        return None

    @staticmethod
    def _first_invoice_url(asaas_subscription_id):
        try:
            payments = Asaas.list_subscription_payments(asaas_subscription_id)
            data = payments.get("data") or []
            if data:
                first = data[0]
                return first.get("invoiceUrl") or first.get("bankSlipUrl") or first.get("transactionReceiptUrl")
        except AsaasError:
            return None
        return None

    @staticmethod
    def checkout(user, data):
        product_type = data.get("product_type") or "plan"
        product_id = data.get("product_id")
        platform = (data.get("platform") or "web").lower()
        billing_type = data.get("billing_type") or "UNDEFINED"
        coupon_code = data.get("coupon_code")
        cpf_cnpj = _normalize_cpf_cnpj(data.get("cpf_cnpj") or getattr(user, "cpf_cnpj", None))
        if not product_id:
            return {"error": "product_id is required"}, 400
        if platform == "ios":
            return {
                "error": "In-app purchases on iOS are not available yet. Please subscribe on the web.",
                "code": "ios_use_web",
            }, 400

        product = BillingService._product(product_type, product_id)
        if not product:
            return {"error": "Product not found"}, 404
        if product_type == "plan" and not product.get("is_active"):
            return {"error": "Plan is not available"}, 400
        if product_type == "book" and product.get("sale_mode") == "plans_only":
            return {"error": "This book is only available through a plan"}, 400
        if product_type == "book" and product.get("is_free"):
            EntitlementService.grant_book(user._id, product["_id"], source="purchase")
            return {"provider": "free", "granted": True, "product_id": product["_id"]}, 200
        if product_type == "bundle" and not product.get("is_published"):
            return {"error": "Bundle is not available"}, 400

        amount = float(product.get("price") or 0)
        coupon = None
        if coupon_code:
            quoted, error = CouponService.quote(amount, coupon_code, product_type, product_id)
            if error:
                return {"error": error}, 400
            coupon = quoted["coupon"]
            amount = quoted["final_amount"]

        use_play = platform == "android" and product_type != "book"
        if use_play:
            return BillingService._android_checkout(user, product_type, product, coupon)
        if not cpf_cnpj:
            return {
                "error": "Informe um CPF ou CNPJ válido para assinar.",
                "code": "cpf_required",
            }, 400

        if product_type == "plan":
            blocking = BillingService._blocking_subscription(user._id)
            if blocking and blocking.get("status") in ACCESS_STATUSES:
                if blocking.get("provider") == "google_play":
                    return {
                        "error": "You already have an active Google Play subscription. Cancel it in the Play Store before subscribing on the web.",
                        "code": "duplicate_subscription",
                        "subscription": blocking,
                    }, 409
                if blocking.get("plan_id") == str(product_id):
                    return {"error": "You already have an active subscription", "code": "duplicate_subscription"}, 409
                return {"error": "Cancel or change your current plan before starting a new one", "code": "duplicate_subscription"}, 409

        try:
            customer_id = BillingService._ensure_asaas_customer(user, cpf_cnpj)
            next_due = Asaas.default_next_due_date(product.get("trial_days") if product_type == "plan" else 0)
            discount = asaas_discount_payload(coupon)
            if product_type == "plan":
                payload = {
                    "customer": customer_id,
                    "billingType": billing_type,
                    "value": amount,
                    "nextDueDate": next_due,
                    "cycle": product.get("cycle") or "MONTHLY",
                    "description": product.get("name"),
                    "externalReference": f"plan:{user._id}:{product['_id']}",
                }
                if int(product.get("trial_days") or 0) > 0:
                    payload["nextDueDate"] = Asaas.default_next_due_date(product.get("trial_days"))
                if discount:
                    payload["discount"] = discount
                asaas_sub = Asaas.create_subscription(payload)
                invoice_url = asaas_sub.get("invoiceUrl") or BillingService._first_invoice_url(asaas_sub.get("id"))
                status = "trialing" if int(product.get("trial_days") or 0) > 0 else "pending"
                subscription = SubscriptionModel.create({
                    "user_id": user._id,
                    "plan_id": product["_id"],
                    "provider": "asaas",
                    "provider_subscription_id": asaas_sub.get("id"),
                    "asaas_customer_id": customer_id,
                    "status": status,
                    "billing_cycle": product.get("cycle"),
                    "value": amount,
                    "original_value": float(product.get("price") or 0),
                    "coupon_id": coupon["_id"] if coupon else None,
                    "payment_method": billing_type,
                    "invoice_url": invoice_url,
                    "next_due_date": next_due,
                    "grace_until": compute_grace_until(next_due),
                    "current_period_start": utcnow(),
                    "current_period_end": utcnow() + cycle_timedelta(product.get("cycle")),
                })
                if coupon:
                    CouponModel.record_redemption(coupon["_id"], user._id, {"subscription_id": subscription["_id"]})
                if status == "trialing":
                    EntitlementService.grant_subscription_entitlements(user._id, product, subscription["_id"])
                return {
                    "provider": "asaas",
                    "checkout_url": invoice_url,
                    "subscription": subscription,
                }, 200

            snapshot = product_snapshot(product_type, product)
            payload = {
                "customer": customer_id,
                "billingType": billing_type,
                "value": amount,
                "dueDate": Asaas.default_next_due_date(0),
                "description": invoice_description(product_type, product),
                "externalReference": f"{product_type}:{user._id}:{product['_id']}",
            }
            if discount:
                payload["discount"] = discount
            asaas_pay = Asaas.create_payment(payload)
            payment = PaymentModel.create({
                "user_id": user._id,
                "type": product_type,
                "provider": "asaas",
                "provider_payment_id": asaas_pay.get("id"),
                "status": "pending",
                "amount": amount,
                "product_type": product_type,
                "product_id": product["_id"],
                "coupon_id": coupon["_id"] if coupon else None,
                "invoice_url": asaas_pay.get("invoiceUrl"),
                "payment_method": billing_type,
                "metadata": {
                    "external_reference": payload["externalReference"],
                    "invoice_description": payload["description"],
                    "product": snapshot,
                },
            })
            if coupon:
                CouponModel.record_redemption(coupon["_id"], user._id, {"payment_id": payment["_id"]})
            return {
                "provider": "asaas",
                "checkout_url": asaas_pay.get("invoiceUrl"),
                "payment": payment,
            }, 200
        except AsaasError as exc:
            return {"error": _asaas_error_message(exc), "code": "asaas_error", "details": exc.payload}, exc.status_code

    @staticmethod
    def _android_checkout(user, product_type, product, coupon):
        blocking = BillingService._blocking_subscription(user._id)
        if product_type == "plan" and blocking and blocking.get("status") in ACCESS_STATUSES:
            if blocking.get("provider") == "asaas":
                return {
                    "error": "You already have an active web subscription. Cancel it before purchasing on Google Play.",
                    "code": "duplicate_subscription",
                    "subscription": blocking,
                }, 409
            if blocking.get("plan_id") == product.get("_id"):
                return {"error": "You already have an active subscription", "code": "duplicate_subscription"}, 409
        sku = product.get("google_play_product_id")
        if not sku:
            return {"error": "This product is not available on Google Play", "code": "missing_sku"}, 400
        return {
            "provider": "google_play",
            "sku": sku,
            "product_type": product_type,
            "product_id": product["_id"],
            "coupon_id": coupon["_id"] if coupon else None,
        }, 200

    @staticmethod
    def handle_asaas_webhook(payload, headers):
        if not Asaas.verify_webhook(headers):
            return {"error": "Invalid webhook token"}, 401
        event_type = payload.get("event") or payload.get("type")
        payment = payload.get("payment") or {}
        subscription_payload = payload.get("subscription") or {}
        event_id = (
            payload.get("id")
            or payment.get("id") and f"{event_type}:{payment.get('id')}"
            or subscription_payload.get("id") and f"{event_type}:{subscription_payload.get('id')}"
        )
        if event_id and WebhookEventModel.already_processed("asaas", event_id):
            return {"message": "already processed"}, 200
        if event_id:
            WebhookEventModel.record("asaas", event_id, event_type, payload)

        if event_type in ("PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"):
            BillingService._on_asaas_payment(payment, "confirmed")
        elif event_type == "PAYMENT_OVERDUE":
            BillingService._on_asaas_payment(payment, "overdue")
        elif event_type in ("PAYMENT_REFUSED", "PAYMENT_DELETED"):
            BillingService._on_asaas_payment(payment, "refused")
        elif event_type in ("PAYMENT_REFUNDED", "PAYMENT_REFUND_DENIED"):
            BillingService._on_asaas_payment(payment, "refunded")
        elif event_type in ("SUBSCRIPTION_DELETED", "SUBSCRIPTION_INACTIVATED"):
            BillingService._on_asaas_subscription_status(subscription_payload, "canceled" if event_type == "SUBSCRIPTION_DELETED" else "suspended")
        elif event_type == "SUBSCRIPTION_UPDATED":
            BillingService._on_asaas_subscription_status(subscription_payload, None)

        return {"message": "ok"}, 200

    @staticmethod
    def _on_asaas_payment(payment_payload, status):
        provider_payment_id = payment_payload.get("id")
        provider_sub_id = payment_payload.get("subscription")
        payment = PaymentModel.get_by_provider_id("asaas", provider_payment_id)
        subscription = SubscriptionModel.get_by_provider_id("asaas", provider_sub_id) if provider_sub_id else None
        if not payment and provider_payment_id:
            user_id = None
            product_type = "subscription" if provider_sub_id else None
            product_id = None
            if subscription:
                user_id = subscription.get("user_id")
                product_type = "plan"
                product_id = subscription.get("plan_id")
            else:
                external = payment_payload.get("externalReference") or ""
                parts = external.split(":")
                if len(parts) == 3:
                    product_type, user_id, product_id = parts
            if user_id:
                payment = PaymentModel.create({
                    "user_id": user_id,
                    "type": "subscription" if provider_sub_id else product_type,
                    "provider": "asaas",
                    "provider_payment_id": provider_payment_id,
                    "status": status,
                    "amount": payment_payload.get("value") or 0,
                    "product_type": product_type,
                    "product_id": product_id,
                    "subscription_id": subscription["_id"] if subscription else None,
                    "invoice_url": payment_payload.get("invoiceUrl"),
                    "payment_method": payment_payload.get("billingType"),
                    "paid_at": utcnow() if status == "confirmed" else None,
                })
        elif payment:
            updates = {
                "status": status,
                "invoice_url": payment_payload.get("invoiceUrl") or payment.get("invoice_url"),
                "payment_method": payment_payload.get("billingType") or payment.get("payment_method"),
            }
            if status == "confirmed":
                updates["paid_at"] = utcnow()
            if status == "refunded":
                updates["refunded_at"] = utcnow()
            payment = PaymentModel.update(payment["_id"], updates)

        if subscription:
            BillingService._apply_subscription_payment(subscription, status, payment_payload)
        elif payment and status == "confirmed":
            BillingService._fulfill_one_time(payment)
        elif payment and status == "refunded":
            BillingService._revoke_one_time(payment)

    @staticmethod
    def _apply_subscription_payment(subscription, status, payment_payload):
        user_id = subscription["user_id"]
        plan = PlanModel.get_by_id(subscription["plan_id"])
        next_due = payment_payload.get("dueDate") or subscription.get("next_due_date")
        updates = {
            "next_due_date": next_due,
            "grace_until": compute_grace_until(next_due),
            "invoice_url": payment_payload.get("invoiceUrl") or subscription.get("invoice_url"),
            "payment_method": payment_payload.get("billingType") or subscription.get("payment_method"),
        }
        if status == "confirmed":
            updates["status"] = "active"
            updates["current_period_start"] = utcnow()
            if plan:
                updates["current_period_end"] = utcnow() + cycle_timedelta(plan.get("cycle"))
            EntitlementService.grant_subscription_entitlements(user_id, plan, subscription["_id"])
        elif status == "overdue":
            updates["status"] = "overdue"
        elif status == "refused":
            updates["status"] = "refused"
        elif status == "refunded":
            updates["status"] = "canceled"
            updates["canceled_at"] = utcnow()
            EntitlementService.revoke_subscription_entitlements(user_id, subscription["_id"])
        SubscriptionModel.update(subscription["_id"], updates)

    @staticmethod
    def _on_asaas_subscription_status(payload, status):
        provider_id = payload.get("id")
        subscription = SubscriptionModel.get_by_provider_id("asaas", provider_id)
        if not subscription:
            return
        updates = {}
        asaas_status = (payload.get("status") or "").upper()
        mapped = status
        if not mapped:
            mapped = {
                "ACTIVE": "active",
                "EXPIRED": "expired",
                "INACTIVE": "suspended",
            }.get(asaas_status)
        if mapped:
            updates["status"] = mapped
            if mapped in ("canceled", "expired", "suspended"):
                updates["canceled_at"] = utcnow()
                EntitlementService.revoke_subscription_entitlements(subscription["user_id"], subscription["_id"])
            elif mapped == "active":
                plan = PlanModel.get_by_id(subscription["plan_id"])
                if plan:
                    EntitlementService.grant_subscription_entitlements(subscription["user_id"], plan, subscription["_id"])
        if payload.get("nextDueDate"):
            updates["next_due_date"] = payload.get("nextDueDate")
            updates["grace_until"] = compute_grace_until(payload.get("nextDueDate"))
        if updates:
            SubscriptionModel.update(subscription["_id"], updates)

    @staticmethod
    def _fulfill_one_time(payment):
        user_id = payment.get("user_id")
        product_type = payment.get("product_type")
        product_id = payment.get("product_id")
        if not user_id or not product_id:
            return
        if product_type == "book":
            EntitlementService.grant_book(user_id, product_id, source="purchase", source_id=payment["_id"])
        elif product_type == "bundle":
            EntitlementService.grant_bundle(user_id, product_id, source="purchase", source_id=payment["_id"])

    @staticmethod
    def _revoke_one_time(payment):
        user_id = payment.get("user_id")
        if not user_id:
            return
        EntitlementModel.revoke_by_source(user_id, "purchase", payment["_id"])

    @staticmethod
    def my_subscription(user):
        return EntitlementService.resolve(user)

    @staticmethod
    def my_payments(user):
        return PaymentModel.list_for_user(user._id)

    @staticmethod
    def sync_payment(user, payment_id):
        payment = PaymentModel.get_by_id(payment_id)
        if not payment or str(payment.get("user_id")) != str(user._id):
            return {"error": "Payment not found"}, 404
        if payment.get("status") == "confirmed":
            BillingService._fulfill_one_time(payment)
            return {"payment": payment, "granted": True}, 200
        if payment.get("provider") != "asaas" or not payment.get("provider_payment_id"):
            return {"payment": payment, "granted": False}, 200
        try:
            asaas_pay = Asaas.get_payment(payment["provider_payment_id"])
        except AsaasError as exc:
            return {"error": _asaas_error_message(exc), "code": "asaas_error", "details": exc.payload}, exc.status_code
        status = (asaas_pay.get("status") or "").upper()
        if status in ("CONFIRMED", "RECEIVED", "RECEIVED_IN_CASH"):
            payment = PaymentModel.update(payment["_id"], {
                "status": "confirmed",
                "paid_at": utcnow(),
                "invoice_url": asaas_pay.get("invoiceUrl") or payment.get("invoice_url"),
                "payment_method": asaas_pay.get("billingType") or payment.get("payment_method"),
            })
            BillingService._fulfill_one_time(payment)
            return {"payment": payment, "granted": True, "asaas_status": status}, 200
        return {"payment": payment, "granted": False, "asaas_status": status}, 200

    @staticmethod
    def cancel_mine(user):
        subscription = BillingService._blocking_subscription(user._id)
        if not subscription:
            return {"error": "No active subscription"}, 404
        if subscription.get("provider") == "google_play":
            return {
                "error": "Cancel this subscription in the Google Play Store",
                "code": "manage_on_play",
            }, 400
        if subscription.get("provider") == "asaas" and subscription.get("provider_subscription_id"):
            try:
                Asaas.cancel_subscription(subscription["provider_subscription_id"])
            except AsaasError as exc:
                return {"error": str(exc)}, exc.status_code
        updated = SubscriptionModel.update(subscription["_id"], {
            "status": "canceled",
            "canceled_at": utcnow(),
        })
        EntitlementService.revoke_subscription_entitlements(user._id, subscription["_id"])
        return {"subscription": updated}, 200

    @staticmethod
    def change_plan(user, plan_id):
        plan = PlanModel.get_by_id(plan_id)
        if not plan or not plan.get("is_active"):
            return {"error": "Plan not found"}, 404
        subscription = BillingService._blocking_subscription(user._id)
        if not subscription:
            return {"error": "No active subscription"}, 404
        if subscription.get("provider") != "asaas":
            return {"error": "Plan changes must be done with the same payment provider"}, 400
        try:
            Asaas.update_subscription(subscription["provider_subscription_id"], {
                "value": float(plan.get("price") or 0),
                "cycle": plan.get("cycle"),
                "description": plan.get("name"),
            })
        except AsaasError as exc:
            return {"error": str(exc)}, exc.status_code
        EntitlementService.revoke_subscription_entitlements(user._id, subscription["_id"])
        updated = SubscriptionModel.update(subscription["_id"], {
            "plan_id": plan["_id"],
            "value": float(plan.get("price") or 0),
            "original_value": float(plan.get("price") or 0),
            "billing_cycle": plan.get("cycle"),
            "status": "active",
        })
        EntitlementService.grant_subscription_entitlements(user._id, plan, subscription["_id"])
        return {"subscription": updated, "plan": plan}, 200

    @staticmethod
    def update_payment_method(user):
        subscription = BillingService._blocking_subscription(user._id)
        if not subscription:
            return {"error": "No active subscription"}, 404
        if subscription.get("provider") == "google_play":
            return {"manage_url": "https://play.google.com/store/account/subscriptions"}, 200
        return {"checkout_url": subscription.get("invoice_url")}, 200

    @staticmethod
    def admin_set_status(admin, subscription_id, status, action=None):
        subscription = SubscriptionModel.get_by_id(subscription_id)
        if not subscription:
            return {"error": "Subscription not found"}, 404
        before = dict(subscription)
        provider_id = subscription.get("provider_subscription_id")
        try:
            if action == "cancel" and subscription.get("provider") == "asaas" and provider_id:
                Asaas.cancel_subscription(provider_id)
                status = "canceled"
            elif action == "suspend":
                status = "suspended"
            elif action == "reactivate" and subscription.get("provider") == "asaas" and provider_id:
                Asaas.update_subscription(provider_id, {"status": "ACTIVE"})
                status = "active"
        except AsaasError as exc:
            return {"error": str(exc)}, exc.status_code
        updates = {"status": status}
        if status in ("canceled", "expired", "suspended"):
            updates["canceled_at"] = utcnow()
            EntitlementService.revoke_subscription_entitlements(subscription["user_id"], subscription["_id"])
        elif status in ACCESS_STATUSES:
            plan = PlanModel.get_by_id(subscription["plan_id"])
            if plan:
                EntitlementService.grant_subscription_entitlements(subscription["user_id"], plan, subscription["_id"])
        updated = SubscriptionModel.update(subscription_id, updates)
        AuditLogModel.record(admin._id, action or f"set_status_{status}", "subscription", subscription_id, before, updated)
        return {"subscription": updated}, 200

    @staticmethod
    def admin_grant(admin, data):
        user_id = data.get("user_id")
        grant_type = data.get("type")
        resource_id = data.get("resource_id")
        notes = data.get("notes") or ""
        if not user_id or not grant_type or not resource_id:
            return {"error": "user_id, type and resource_id are required"}, 400
        if grant_type == "plan":
            result = EntitlementService.grant_plan_manual(user_id, resource_id, granted_by=admin._id, notes=notes)
        elif grant_type == "book":
            result = EntitlementService.grant_book(user_id, resource_id, source="manual", granted_by=admin._id, notes=notes)
        elif grant_type == "bundle":
            result = EntitlementService.grant_bundle(user_id, resource_id, source="manual", granted_by=admin._id, notes=notes)
        elif grant_type == "service":
            result = EntitlementModel.grant({
                "user_id": user_id,
                "type": "service",
                "resource_id": resource_id,
                "source": "manual",
                "granted_by": admin._id,
                "notes": notes,
            })
        else:
            return {"error": "Invalid grant type"}, 400
        AuditLogModel.record(admin._id, "grant", grant_type, resource_id, None, result)
        return {"grant": result}, 200

    @staticmethod
    def admin_revoke(admin, entitlement_id):
        before = EntitlementModel.get_by_id(entitlement_id)
        if not before:
            return {"error": "Entitlement not found"}, 404
        result = EntitlementService.revoke_entitlement(entitlement_id, notes="revoked by admin")
        AuditLogModel.record(admin._id, "revoke", before.get("type"), entitlement_id, before, result)
        return {"entitlement": result}, 200

    @staticmethod
    def register_external_sale(admin, data):
        email = (data.get("email") or "").strip().lower()
        if not email:
            return {"error": "email is required"}, 400
        product_type = data.get("product_type")
        product_ids = data.get("product_ids") or []
        if data.get("product_id"):
            product_ids = [data.get("product_id")]
        if not product_type or not product_ids:
            return {"error": "product_type and product_ids are required"}, 400
        created = False
        user = UserModel.find_by_email(email)
        if not user:
            user = UserModel.create_pending_user(data.get("name"), email)
            created = True
            BillingService._send_access_invite(email, data.get("name") or "")
        grants = []
        for product_id in product_ids:
            if product_type == "plan":
                grants.append(EntitlementService.grant_plan_manual(user._id, product_id, granted_by=admin._id, notes="external sale"))
            elif product_type == "book":
                grants.append(EntitlementService.grant_book(user._id, product_id, source="external", granted_by=admin._id, notes="external sale"))
            elif product_type == "bundle":
                grants.append(EntitlementService.grant_bundle(user._id, product_id, source="external", granted_by=admin._id, notes="external sale"))
            elif product_type == "service":
                grants.append(EntitlementModel.grant({
                    "user_id": user._id,
                    "type": "service",
                    "resource_id": product_id,
                    "source": "external",
                    "granted_by": admin._id,
                    "notes": "external sale",
                }))
        sale = ExternalSaleModel.create({
            "email": email,
            "name": data.get("name") or user.name,
            "user_id": user._id,
            "product_type": product_type,
            "product_ids": product_ids,
            "amount": data.get("amount"),
            "origin": data.get("origin") or "external",
            "notes": data.get("notes") or "",
            "invite_sent": created,
            "created_by": admin._id,
        })
        PaymentModel.create({
            "user_id": user._id,
            "type": product_type,
            "provider": "external",
            "status": "confirmed",
            "amount": data.get("amount") or 0,
            "product_type": product_type,
            "product_id": product_ids[0],
            "paid_at": utcnow(),
            "origin": "external",
            "metadata": {"sale_id": sale["_id"], "product_ids": product_ids},
        })
        AuditLogModel.record(admin._id, "external_sale", product_type, sale["_id"], None, sale)
        return {"sale": sale, "user_created": created, "grants": grants}, 201

    @staticmethod
    def _send_access_invite(email, name):
        try:
            msg = Message(
                subject="Você recebeu acesso ao Memobelc",
                recipients=[email],
                sender=Config.MAIL_DEFAULT_SENDER or Config.MAIL_USERNAME,
            )
            msg.body = f"""
Olá {name or ''}!

Uma compra foi registrada para você na plataforma Memobelc.
Para concluir seu cadastro e acessar o conteúdo, use este e-mail em:
{Config.FRONT_BASE_URL}/register

Se já possuir conta, faça login em:
{Config.FRONT_BASE_URL}/login

Equipe Memobelc
"""
            mail.send(msg)
        except Exception as exc:
            current_app.logger.error(f"Failed to send external sale invite: {exc}")

    @staticmethod
    def verify_google_purchase(user, data):
        sku = data.get("sku") or data.get("productId")
        token = data.get("purchase_token") or data.get("purchaseToken")
        product_type = data.get("product_type") or "plan"
        if not sku or not token:
            return {"error": "sku and purchase_token are required"}, 400
        if WebhookEventModel.already_processed("google_play", token):
            existing = SubscriptionModel.get_by_provider_id("google_play", token) or PaymentModel.get_by_provider_id("google_play", token)
            return {"message": "already processed", "record": existing}, 200
        try:
            if product_type == "plan":
                payload = GooglePlay.verify_subscription(sku, token)
            else:
                payload = GooglePlay.verify_product(sku, token)
        except GooglePlayError as exc:
            return {"error": str(exc)}, exc.status_code

        WebhookEventModel.record("google_play", token, "VERIFY", payload)
        if product_type == "plan":
            blocking = BillingService._blocking_subscription(user._id)
            if blocking and blocking.get("provider") == "asaas" and blocking.get("status") in ACCESS_STATUSES:
                return {
                    "error": "You already have an active Asaas subscription",
                    "code": "duplicate_subscription",
                }, 409
            plan = PlanModel.get_by_google_sku(sku)
            if not plan:
                return {"error": "Unknown Google Play SKU"}, 404
            expiry_ms = payload.get("expiryTimeMillis")
            expiry = datetime.fromtimestamp(int(expiry_ms) / 1000, tz=timezone.utc) if expiry_ms else utcnow() + timedelta(days=30)
            payment_state = str(payload.get("paymentState"))
            status = "active" if payment_state in ("1", "2") else "pending"
            if payload.get("autoRenewing") is False and expiry <= utcnow():
                status = "expired"
            subscription = SubscriptionModel.get_by_provider_id("google_play", token)
            if not subscription:
                subscription = SubscriptionModel.create({
                    "user_id": user._id,
                    "plan_id": plan["_id"],
                    "provider": "google_play",
                    "provider_subscription_id": token,
                    "status": status,
                    "billing_cycle": plan.get("cycle"),
                    "value": float(plan.get("price") or 0),
                    "original_value": float(plan.get("price") or 0),
                    "next_due_date": expiry,
                    "grace_until": compute_grace_until(expiry),
                    "current_period_end": expiry,
                    "metadata": {"sku": sku, "order_id": payload.get("orderId")},
                })
            else:
                subscription = SubscriptionModel.update(subscription["_id"], {
                    "status": status,
                    "next_due_date": expiry,
                    "grace_until": compute_grace_until(expiry),
                    "current_period_end": expiry,
                })
            PaymentModel.create({
                "user_id": user._id,
                "type": "subscription",
                "provider": "google_play",
                "provider_payment_id": payload.get("orderId") or token,
                "status": "confirmed" if status in ACCESS_STATUSES else "pending",
                "amount": plan.get("price") or 0,
                "product_type": "plan",
                "product_id": plan["_id"],
                "subscription_id": subscription["_id"],
                "paid_at": utcnow() if status in ACCESS_STATUSES else None,
            })
            if status in ACCESS_STATUSES:
                EntitlementService.grant_subscription_entitlements(user._id, plan, subscription["_id"])
            try:
                GooglePlay.acknowledge_subscription(sku, token)
            except GooglePlayError:
                pass
            return {"subscription": subscription, "provider": "google_play"}, 200

        product = BookModel.get_by_google_sku(sku) if product_type == "book" else BookBundleModel.get_by_google_sku(sku)
        if not product:
            return {"error": "Unknown Google Play SKU"}, 404
        payment = PaymentModel.create({
            "user_id": user._id,
            "type": product_type,
            "provider": "google_play",
            "provider_payment_id": token,
            "status": "confirmed",
            "amount": product.get("price") or 0,
            "product_type": product_type,
            "product_id": product["_id"],
            "paid_at": utcnow(),
            "metadata": {"sku": sku},
        })
        BillingService._fulfill_one_time(payment)
        try:
            GooglePlay.acknowledge_product(sku, token)
        except GooglePlayError:
            pass
        return {"payment": payment, "provider": "google_play"}, 200

    @staticmethod
    def handle_google_rtdn(body, token=None):
        if not GooglePlay.verify_rtdn_token(token):
            return {"error": "Invalid RTDN token"}, 401
        notification = GooglePlay.decode_rtdn(body)
        event_id = (notification.get("message") or {}).get("messageId") or notification.get("eventTimeMillis")
        if event_id and WebhookEventModel.already_processed("google_play_rtdn", event_id):
            return {"message": "already processed"}, 200
        if event_id:
            WebhookEventModel.record("google_play_rtdn", event_id, "RTDN", notification)
        sub_n = notification.get("subscriptionNotification") or {}
        one_n = notification.get("oneTimeProductNotification") or {}
        purchase_token = sub_n.get("purchaseToken") or one_n.get("purchaseToken")
        sku = sub_n.get("subscriptionId") or one_n.get("sku")
        ntype = sub_n.get("notificationType")
        if purchase_token and sku and ntype is not None:
            subscription = SubscriptionModel.get_by_provider_id("google_play", purchase_token)
            status_map = {
                2: "active",
                3: "canceled",
                4: "active",
                5: "overdue",
                6: "suspended",
                10: "paused",
                12: "expired",
                13: "expired",
            }
            mapped = status_map.get(int(ntype))
            if subscription and mapped:
                if mapped in ("canceled", "expired", "suspended"):
                    EntitlementService.revoke_subscription_entitlements(subscription["user_id"], subscription["_id"])
                    SubscriptionModel.update(subscription["_id"], {"status": mapped if mapped != "paused" else "suspended", "canceled_at": utcnow()})
                elif mapped == "active":
                    plan = PlanModel.get_by_id(subscription["plan_id"])
                    SubscriptionModel.update(subscription["_id"], {"status": "active"})
                    if plan:
                        EntitlementService.grant_subscription_entitlements(subscription["user_id"], plan, subscription["_id"])
                elif mapped == "overdue":
                    SubscriptionModel.update(subscription["_id"], {"status": "overdue"})
        return {"message": "ok"}, 200

    @staticmethod
    def reconcile():
        now = utcnow()
        for subscription in SubscriptionModel.query({"status": "active"}, limit=200)[0]:
            grace = parse_datetime(subscription.get("grace_until"))
            due = parse_datetime(subscription.get("next_due_date"))
            if due and now > due and grace and now > grace:
                SubscriptionModel.update(subscription["_id"], {"status": "overdue"})
            if subscription.get("provider") == "asaas" and subscription.get("provider_subscription_id") and Asaas.is_configured():
                try:
                    remote = Asaas.get_subscription(subscription["provider_subscription_id"])
                    BillingService._on_asaas_subscription_status(remote, None)
                except AsaasError:
                    continue
        return True
