# Stripe Integration Setup

This guide covers setting up Stripe for NeuroSim's Pro tier subscriptions.

## 1. Create Stripe Account & Products

1. Sign up at [stripe.com](https://stripe.com) (or log in).
2. Go to **Products** → **Add Product**.
3. Create **two pricing models**:

| Product | Price (Monthly) | Price (Yearly) |
|---------|----------------|----------------|
| NeuroSim Pro | $29.00 / month | $290.00 / year |

4. For each price, click **Activate price** and copy the **Price ID** (looks like `price_abc123...`).

## 2. Set Environment Variables

Add these to your backend `.env` file or Render dashboard:

```bash
# Required
STRIPE_SECRET_KEY=sk_live_...              # from Stripe Dashboard → Developers → API keys
STRIPE_PRICE_ID_MONTHLY=price_abc123...    # monthly Price ID from step 1
STRIPE_PRICE_ID_YEARLY=price_def456...     # yearly Price ID from step 1

# Required for webhook signature verification
STRIPE_WEBHOOK_SECRET=whsec_...            # created in step 3

# Optional — enables Pro tier
PREMIUM_ENABLED=true
```

> **⚠️ Never commit `.env` files or expose secret keys.** Use Render's dashboard → Environment Variables for production.

## 3. Configure Webhook Endpoint

1. Go to Stripe Dashboard → **Developers** → **Webhooks** → **Add endpoint**.
2. **Endpoint URL**: `https://your-app.com/api/stripe/webhook`
   - For local testing: use [Stripe CLI](https://stripe.com/docs/stripe-cli) → `stripe listen --forward-to localhost:8000/api/stripe/webhook`
3. **Events to send**:
   - `checkout.session.completed` — activates premium for the user
   - `customer.subscription.deleted` — deactivates premium
   - `invoice.payment_failed` — logs payment alerts
4. After creating, copy the **Signing secret** (`whsec_...`) and set `STRIPE_WEBHOOK_SECRET`.

## 4. Verify Integration

### Check the backend is ready:

```bash
curl https://your-app.com/api/premium/status
```

Expected response:
```json
{
  "enabled": true,
  "stripe_configured": true,
  "stripe_price_id_monthly": "price_abc123...",
  "stripe_price_id_yearly": "price_def456..."
}
```

### Create a checkout session (test):

Replace `price_abc123` with a real Price ID (use `price_...` from Stripe test mode first):

```bash
curl -X POST https://your-app.com/api/stripe/create-checkout-session \
  -H "Content-Type: application/json" \
  -d '{
    "price_id": "price_abc123",
    "success_url": "https://your-app.com/dashboard",
    "cancel_url": "https://your-app.com/pricing",
    "user_id": "demo-user"
  }'
```

Expected response:
```json
{
  "url": "https://checkout.stripe.com/c/pay_...",
  "session_id": "cs_test_..."
}
```

### Test the webhook (local):

```bash
stripe trigger checkout.session.completed \
  --add payment_intent:metadata.user_id=demo-user
```

## 5. Frontend Behavior

The pricing page (`/pricing`) automatically:

- **Fetches** premium status from the backend on mount
- **Stripe configured** → Pro CTA shows "Upgrade to Pro" and opens Stripe Checkout
- **Stripe not configured** → Pro CTA shows "Join Waitlist" and redirects to `/waitlist`
- **Loading state** → Button shows a spinner during checkout redirect

## Verifying Premium Activation

When a checkout completes:

1. Stripe sends `checkout.session.completed` to `/api/stripe/webhook`
2. The webhook reads `session.metadata.user_id` to identify the user
3. The user is added to the `_premium_users` set (in-memory)
4. Premium usage endpoint at `/api/premium/usage/{user_id}` returns `is_premium: true`

> **Note:** Premium status is stored in-memory and resets on server restart. For production, persist this to Supabase or your database.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Stripe not configured` error | `STRIPE_SECRET_KEY` not set | Add to `.env` or Render env vars |
| `Invalid signature` on webhook | `STRIPE_WEBHOOK_SECRET` mismatch | Re-check the signing secret from Stripe Dashboard |
| Checkout opens but says "No price" | Price ID is from different mode (test vs live) | Ensure Price ID matches your Stripe mode |
| Premium not activated after checkout | `user_id` metadata missing from session | Check webhook logs — ensure metadata is passed |
