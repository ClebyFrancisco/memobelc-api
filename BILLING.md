# Billing: Asaas + Google Play

This document describes the monetization architecture of MemoBelc.

## Decisions

- **Asaas is the primary provider** for the web app: subscriptions, **one-time book purchases (invoice includes title, author, language, level, genre and chapters)**, bundle purchases, PIX/boleto/card, coupons and refunds. After `PAYMENT_CONFIRMED` or a client sync, the book is granted to the buyer's library.
- **Google Play Billing is required on Android** for digital goods sold inside the store listing. The app never offers Asaas checkout on Android for plans/books that have a Play SKU.
- **Stripe is disabled.** `STRIPE_*` variables are optional. `/payment/payment_intent` returns `410`.
- **iOS StoreKit is not implemented in this release.** The Android/iOS app should send users to the website to subscribe until Apple IAP is added. Offering Asaas inside an iOS binary can violate App Store rules for digital goods.

## How access works

Entitlements are the single source of truth. A user can access a service or book if **any** of these is valid:

1. An active/trialing subscription (Asaas or Google Play), including a 48h grace window after `next_due_date` when status is pending/overdue.
2. A confirmed one-time purchase.
3. A manual grant from an admin.
4. An external sale recorded by an admin.

There is **at most one paid active subscription per user**. Upgrade/downgrade stays on the same provider. Switching Asaas ↔ Play requires cancelling the current subscription first.

## Asaas vs Google Play

| Topic | Asaas (web) | Google Play (Android) |
|-------|-------------|------------------------|
| Catalog | Plans and prices in MongoDB | SKUs created in Play Console (`google_play_product_id`) |
| Checkout | Invoice / PIX / card URL from Asaas | `react-native-iap` BillingClient |
| Coupons | Platform coupons applied as Asaas `discount` | Play promo codes only (do not mix) |
| Cancel | API + user area | Play Store subscription management |
| Webhooks | `POST /billing/asaas/webhook` | `POST /billing/google/rtdn` (Pub/Sub) |
| Fees | Asaas processing fees | Google Play commission |

## Environment variables

```
ASAAS_API_KEY=
ASAAS_API_URL=https://api-sandbox.asaas.com/v3
ASAAS_WEBHOOK_TOKEN=

GOOGLE_PLAY_PACKAGE_NAME=com.anonymous.memobelc
GOOGLE_PLAY_SERVICE_ACCOUNT_JSON=
GOOGLE_PLAY_SERVICE_ACCOUNT_FILE=
GOOGLE_PLAY_RTDN_TOKEN=

STRIPE_SECRET_KEY=
STRIPE_WHSEC=
PRICE_ID=
```

Production Asaas URL: `https://api.asaas.com/v3`.

## External setup

1. Create an Asaas account (sandbox then production).
2. Register a webhook pointing to `{API_URL}/billing/asaas/webhook` with header token `ASAAS_WEBHOOK_TOKEN`. Subscribe to payment and subscription events.
3. In Google Play Console, create subscription/in-app products whose IDs match `google_play_product_id` on plans/books/bundles.
4. Create a service account with Android Publisher access and store the JSON in `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` or a file path.
5. Configure Real-time Developer Notifications (Pub/Sub push) to `{API_URL}/billing/google/rtdn?token={GOOGLE_PLAY_RTDN_TOKEN}`.
6. Android builds must be EAS development/production builds; Expo Go cannot run Play Billing.

## Main API routes

- `GET /plans/public` — catalog
- `POST /billing/checkout` — `{ product_type, product_id, platform, coupon_code, billing_type }`
- `GET /billing/me` and `GET /entitlements/me`
- `POST /billing/cancel`, `POST /billing/change-plan`
- `POST /billing/google/verify` — `{ sku, purchase_token, product_type }`
- Admin: `/plans/admin`, `/coupons/admin`, `/bundles/admin`, `/admin/billing/*`

Default service visibility is **allow for everyone**. Admin can set each service to **allow** (visible to everyone), **disabled** (visible, not clickable), **disabled_upgrade** (paywalled until the user has an active plan), or **hide** (not shown in the menu). `redirect_plans` is treated as `disabled_upgrade`.
