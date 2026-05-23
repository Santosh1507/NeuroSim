"""Subscription status and usage tracking endpoints.

Returns the user's current plan, analysis usage this month,
remaining quota, and period reset date. Works with both
in-memory fallback and Supabase-backed storage.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from config import settings
from rate_limiter import check_api_limit
from shared_state import _usage_tracker, _usage_tracker_month, _is_premium, require_auth_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["subscription"])


@router.get("/subscription/status")
async def subscription_status(user_id: str = Depends(require_auth_user)):
    """Return the user's current subscription plan, usage, and limits."""
    used = _usage_tracker.get(user_id, 0)
    is_premium = _is_premium(user_id)
    limit = settings.premium_max_analyses_free

    # Calculate period end (end of current month)
    now = datetime.now(timezone.utc)
    if _usage_tracker_month == now.month:
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period_start.month == 12:
        period_end = period_start.replace(year=period_start.year + 1, month=1)
    else:
        period_end = period_start.replace(month=period_start.month + 1)

    return {
        "plan": "pro" if is_premium else "free",
        "analyses_used": used,
        "analyses_limit": None if is_premium else limit,
        "remaining": -1 if is_premium else max(0, limit - used),
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "is_premium": is_premium,
        "premium_enabled": settings.premium_enabled,
    }
