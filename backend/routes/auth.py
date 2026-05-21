"""Authentication routes — Supabase email/password sign-up, sign-in, and guest merge."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config import settings
from shared_state import require_auth_user
from storage_adapter import _supabase

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


class SignUpRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class SignInRequest(BaseModel):
    email: str
    password: str


class GuestMergeRequest(BaseModel):
    guest_id: Optional[str] = None
    guest_session_id: Optional[str] = None


class AuthResponse(BaseModel):
    user_id: str
    email: str
    access_token: Optional[str] = None
    message: str


@router.post("/auth/sign-up", response_model=AuthResponse)
async def sign_up(req: SignUpRequest):
    """Create a new user account via Supabase Auth."""
    if not _supabase.enabled:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

    try:
        result = _supabase.client.auth.sign_up({
            "email": req.email,
            "password": req.password,
            "options": {"data": {"name": req.name}},
        })

        if result.user:
            logger.info(f"[AUTH] New user signed up: {req.email} (id={result.user.id})")
            return AuthResponse(
                user_id=result.user.id,
                email=req.email,
                access_token=result.session.access_token if result.session else None,
                message="Account created. Check your email to confirm."
                if not result.user.email_confirmed_at
                else "Account created successfully.",
            )
        raise HTTPException(status_code=400, detail="Sign-up failed")
    except Exception as e:
        error_msg = str(e)
        if "User already registered" in error_msg or "already registered" in error_msg.lower():
            raise HTTPException(status_code=409, detail="Email already registered")
        logger.error(f"[AUTH] Sign-up error: {e}")
        raise HTTPException(status_code=400, detail=f"Sign-up failed: {error_msg}")


@router.post("/auth/sign-in", response_model=AuthResponse)
async def sign_in(req: SignInRequest):
    """Authenticate with email and password."""
    if not _supabase.enabled:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

    try:
        result = _supabase.client.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password,
        })

        if result.user:
            logger.info(f"[AUTH] User signed in: {req.email} (id={result.user.id})")
            return AuthResponse(
                user_id=result.user.id,
                email=req.email,
                access_token=result.session.access_token,
                message="Signed in successfully.",
            )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg or "invalid" in error_msg.lower():
            raise HTTPException(status_code=401, detail="Invalid email or password")
        logger.error(f"[AUTH] Sign-in error: {e}")
        raise HTTPException(status_code=400, detail=f"Sign-in failed: {error_msg}")


@router.post("/auth/sign-out")
async def sign_out(authorization: Optional[str] = None):
    """Sign out the current user."""
    if not _supabase.enabled:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

    try:
        _supabase.client.auth.sign_out()
        return {"message": "Signed out successfully."}
    except Exception as e:
        logger.error(f"[AUTH] Sign-out error: {e}")
        raise HTTPException(status_code=400, detail=f"Sign-out failed: {e}")


@router.post("/auth/guest/merge")
async def merge_guest(req: GuestMergeRequest, user_id: str = Depends(require_auth_user)):
    """Merge guest data (videos, analyses) into the authenticated user account."""
    from storage_adapter import store

    if user_id == "anonymous":
        raise HTTPException(status_code=401, detail="Must be authenticated to merge guest data")

    guest_id = req.guest_id or req.guest_session_id
    if not guest_id:
        raise HTTPException(status_code=400, detail="Missing guest_id or guest_session_id")
    if not guest_id.startswith("guest_"):
        raise HTTPException(status_code=400, detail="Invalid guest ID format")

    merged_count = 0
    try:
        # list_videos() returns List[Dict], not {"videos": [...]}
        all_videos: list = await store.list_videos()
        guest_videos = [v for v in all_videos if v.get("user_id") == guest_id]

        for video in guest_videos:
            vid_id = video.get("id")
            if not vid_id:
                continue

            # Reassign ownership: overwrite cache record with updated user_id
            video["user_id"] = user_id
            from storage_adapter import _videos_cache, _touch_cache
            _videos_cache[vid_id] = video
            _touch_cache(f"v:{vid_id}")

            # Also update in Supabase if available
            if _supabase.enabled:
                try:
                    _supabase.client.table("videos").update({"user_id": user_id}).eq("id", vid_id).execute()
                except Exception as e:
                    logger.warning(f"[AUTH] Guest merge: Supabase video update failed for {vid_id}: {e}")

            # Reassign ownership for the associated analysis
            from storage_adapter import _analyses_cache
            analysis = await store.get_analysis(vid_id)
            if analysis:
                analysis["user_id"] = user_id
                _analyses_cache[vid_id] = analysis
                _touch_cache(f"a:{vid_id}")
                if _supabase.enabled:
                    try:
                        _supabase.client.table("analyses").update({"user_id": user_id}).eq("video_id", vid_id).execute()
                    except Exception as e:
                        logger.warning(f"[AUTH] Guest merge: Supabase analysis update failed for {vid_id}: {e}")

            merged_count += 1

        logger.info(f"[AUTH] Guest merge: {guest_id} → {user_id}, {merged_count} videos merged")
        return {
            "message": f"Merged {merged_count} videos from guest session.",
            "merged_videos": merged_count,
            "new_user_id": user_id,
        }
    except Exception as e:
        logger.error(f"[AUTH] Guest merge error: {e}")
        raise HTTPException(status_code=500, detail=f"Merge failed: {e}")

