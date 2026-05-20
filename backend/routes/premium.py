import logging
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from config import settings
from rate_limiter import check_api_limit
from shared_state import (
    _premium_users,
    _usage_tracker,
    _is_premium,
    get_verified_user_id,
)

logger = logging.getLogger(__name__)

stripe.api_key = settings.stripe_secret_key or ""


class CreateCheckoutSessionRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str
    user_id: Optional[str] = None


router = APIRouter(tags=["premium"])


@router.post("/api/stripe/create-checkout-session")
async def create_checkout_session(
    req: CreateCheckoutSessionRequest,
    verified_user_id: str = Depends(get_verified_user_id),
):
    """Create a Stripe Checkout session for the selected plan."""
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=501, detail="Stripe not configured — set STRIPE_SECRET_KEY")
    try:
        auth_user_id = verified_user_id if verified_user_id != "anonymous" else req.user_id
        metadata = {}
        if auth_user_id:
            metadata["user_id"] = auth_user_id
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": req.price_id, "quantity": 1}],
            success_url=req.success_url,
            cancel_url=req.cancel_url,
            metadata=metadata or None,
        )
        return {"url": session.url, "session_id": session.id}
    except stripe.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {e}")


@router.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """Receive Stripe webhook events for subscription lifecycle."""
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=501, detail="Stripe webhook not configured — set STRIPE_WEBHOOK_SECRET")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id", "")
        if user_id:
            _premium_users.add(user_id)
            logger.info(f"[STRIPE] Premium activated for user {user_id}")

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        user_id = subscription.get("metadata", {}).get("user_id", "")
        if user_id and user_id in _premium_users:
            _premium_users.discard(user_id)
            logger.info(f"[STRIPE] Premium deactivated for user {user_id}")
        logger.info(f"[STRIPE] Subscription {subscription.get('id', 'unknown')} deleted")

    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        logger.warning(f"[STRIPE] Payment failed for invoice {invoice.get('id', 'unknown')}")

    return {"status": "ok"}


@router.get("/api/premium/status")
async def premium_status(_=Depends(check_api_limit)):
    return {
        "enabled": settings.premium_enabled,
        "price_monthly": settings.premium_price_monthly,
        "price_yearly": settings.premium_price_yearly,
        "max_analyses_free": settings.premium_max_analyses_free,
        "gpu_provider": settings.gpu_provider,
        "stripe_price_id_monthly": settings.stripe_price_id_monthly or None,
        "stripe_price_id_yearly": settings.stripe_price_id_yearly or None,
        "stripe_configured": bool(settings.stripe_secret_key),
    }


@router.get("/api/premium/usage/{user_id}")
async def premium_usage(user_id: str):
    count = _usage_tracker.get(user_id, 0)
    is_premium_user = _is_premium(user_id)
    remaining = settings.premium_max_analyses_free - count if not is_premium_user else -1
    return {
        "analyses_this_month": count,
        "limit": settings.premium_max_analyses_free,
        "remaining": remaining,
        "is_premium": is_premium_user,
    }
