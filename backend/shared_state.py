"""Shared state for NeuroSim API — extracted from main.py to avoid circular imports."""
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import jwt
from fastapi import Depends, Header, HTTPException

from config import settings

logger = logging.getLogger(__name__)

# ─── In-memory state ───────────────────────────────────────
_task_status: Dict[str, dict] = {}
_share_links: Dict[str, str] = {}
_video_share_links: Dict[str, list] = {}
_share_link_timestamps: Dict[str, float] = {}
_SHARE_LINK_TTL = 604800  # 7 days
_waitlist: List[Dict[str, Any]] = []
_digest_subs: Dict[str, dict] = {}
_usage_tracker: Dict[str, int] = {}
_usage_tracker_month: int = datetime.now().month
_premium_users: set = set()
_ws_connections: Dict[str, list] = {}
_share_permissions: Dict[str, dict] = {}

# ─── JWT Auth ──────────────────────────────────────────────
_JWT_SECRET = settings.supabase_jwt_secret or os.getenv("SUPABASE_JWT_SECRET", "")
_ALLOW_ANONYMOUS_AUTH = os.getenv("ALLOW_ANONYMOUS_AUTH", "").lower() in ("true", "1", "yes")
# When True, require_auth_user enforces strict JWT validation even in pytest/dev mode.
# Set by _set_jwt_secret_for_test() so auth unit-tests can explicitly test rejection paths.
_FORCE_JWT_AUTH_FOR_TEST: bool = False


async def get_verified_user_id(
    authorization: Optional[str] = Header(None),
    user_id: str = "anonymous",
) -> str:
    """Validate JWT from Authorization header and return verified user_id."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
        if _JWT_SECRET:
            try:
                payload = jwt.decode(
                    token,
                    _JWT_SECRET,
                    algorithms=["HS256"],
                    audience="authenticated",
                    options={"require": ["sub", "exp"]},
                )
                return payload.get("sub", user_id)
            except jwt.ExpiredSignatureError:
                logger.warning(f"[AUTH] Expired token for user_id={user_id}")
            except jwt.InvalidTokenError as e:
                logger.warning(f"[AUTH] Invalid token: {e}")
        elif _ALLOW_ANONYMOUS_AUTH:
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                return payload.get("sub", user_id)
            except Exception:
                return token or user_id
    return user_id


async def require_auth_user(
    authorization: Optional[str] = Header(None),
) -> str:
    """Require a valid JWT and return the authenticated user ID."""
    # Dev/test bypass: allow anonymous access when ALLOW_ANONYMOUS_AUTH=true or
    # running under pytest — UNLESS _FORCE_JWT_AUTH_FOR_TEST is set (which
    # auth unit-tests use to explicitly exercise the 401 rejection paths).
    is_dev_or_test = (_ALLOW_ANONYMOUS_AUTH or "PYTEST_CURRENT_TEST" in os.environ) and not _FORCE_JWT_AUTH_FOR_TEST
    if is_dev_or_test:
        if authorization and authorization.startswith("Bearer "):
            token = authorization.removeprefix("Bearer ")
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                return payload.get("sub", "demo-user")
            except Exception:
                # Non-JWT bearer token (e.g. "dummy") — just return it as user id
                return token or "demo-user"
        if not _JWT_SECRET:
            logger.warning("[AUTH] JWT secret not configured — allowing anonymous access (dev/test mode)")
        return "anonymous"

    if not _JWT_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Authentication not configured. Set SUPABASE_JWT_SECRET or ALLOW_ANONYMOUS_AUTH=true for dev mode."
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(
            token,
            _JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"require": ["sub", "exp"]},
        )
        return payload.get("sub", "")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def _set_jwt_secret_for_test(secret: str) -> None:
    """Override JWT secret for testing. NOT for production use.

    When `secret` is non-empty, also sets _FORCE_JWT_AUTH_FOR_TEST=True so that
    require_auth_user enforces real JWT validation even inside the pytest runner.
    Clear it by calling _set_jwt_secret_for_test("").
    """
    global _JWT_SECRET, _FORCE_JWT_AUTH_FOR_TEST
    _JWT_SECRET = secret
    _FORCE_JWT_AUTH_FOR_TEST = bool(secret)


# ─── Helpers ───────────────────────────────────────────────
from storage_adapter import _evict_stale


def _is_premium(user_id: str) -> bool:
    return user_id in _premium_users


def _increment_usage(user_id: str):
    global _usage_tracker_month
    current_month = datetime.now().month
    if current_month != _usage_tracker_month:
        _usage_tracker.clear()
        _usage_tracker_month = current_month
    if user_id and user_id != "anonymous":
        _usage_tracker[user_id] = _usage_tracker.get(user_id, 0) + 1


async def _get_analysis_or_404(video_id: str) -> Dict[str, Any]:
    """Fetch analysis from store. Raises 404 if not found."""
    from storage_adapter import store
    analysis = await store.get_analysis(video_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


async def _get_video_or_404(video_id: str) -> Dict[str, Any]:
    """Fetch video from store. Raises 404 if not found."""
    from storage_adapter import store
    video = await store.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
