import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from storage_adapter import store, _videos_cache, _supabase
from shared_state import (
    _evict_stale,
    _get_analysis_or_404,
    _share_links,
    _video_share_links,
    _share_link_timestamps,
    _SHARE_LINK_TTL,
    require_auth_user,
)


class ShareRequest(BaseModel):
    video_id: str


class MergeRequest(BaseModel):
    guest_session_id: str
    user_id: str


router = APIRouter(tags=["share"])


@router.post("/api/share")
async def create_share_link(req: ShareRequest, user_id: str = Depends(require_auth_user)):
    _evict_stale()
    analysis = await store.get_analysis(req.video_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    share_id = str(uuid.uuid4())
    _share_links[share_id] = req.video_id
    _share_link_timestamps[share_id] = datetime.now().timestamp()
    _video_share_links.setdefault(req.video_id, []).append(share_id)
    return {"share_id": share_id, "url": f"/r/{share_id}"}


@router.get("/api/share/{share_id}")
async def get_shared_analysis(share_id: str):
    video_id = _share_links.get(share_id)
    if not video_id:
        raise HTTPException(status_code=404, detail="Share link not found")
    ts = _share_link_timestamps.get(share_id, 0)
    if datetime.now().timestamp() - ts > _SHARE_LINK_TTL:
        _share_links.pop(share_id, None)
        _share_link_timestamps.pop(share_id, None)
        raise HTTPException(status_code=410, detail="Share link has expired (links expire after 7 days)")
    analysis = await _get_analysis_or_404(video_id)
    return {"share_id": share_id, "video_id": video_id, "analysis": analysis}


@router.post("/api/merge")
async def merge_guest_session(
    req: MergeRequest,
    user_id: str = Depends(require_auth_user),
):
    """Reassign guest videos/analyses to a newly signed-up user."""
    if user_id != "anonymous" and req.user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot merge into another user's account")
    merged_count = 0
    if True:
        if _supabase.enabled:
            try:
                await (
                    _supabase.client.table("videos")
                    .update({"user_id": req.user_id})
                    .eq("user_id", req.guest_session_id)
                    .execute()
                )
                await (
                    _supabase.client.table("analyses")
                    .update({"user_id": req.user_id})
                    .eq("user_id", req.guest_session_id)
                    .execute()
                )
            except Exception as e:
                print(f"[WARN] Supabase merge failed: {e}")
        for vid, v in _videos_cache.items():
            if v.get("user_id") == req.guest_session_id:
                v["user_id"] = req.user_id
                merged_count += 1

    return {"message": "Session merged", "videos_reassigned": merged_count}
