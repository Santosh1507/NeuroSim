from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from storage_adapter import store
from rate_limiter import check_api_limit
from pdf_report import generate_pdf_report
from shared_state import (
    _get_analysis_or_404,
    _get_video_or_404,
    _task_status,
    _ws_connections,
    _share_links,
    _video_share_links,
    _share_link_timestamps,
    require_auth_user,
)


router = APIRouter(tags=["analysis"])


@router.get("/analyses/{video_id}")
async def get_analysis(video_id: str, _=Depends(check_api_limit)):
    return await _get_analysis_or_404(video_id)


@router.delete("/analyses/{video_id}")
async def delete_analysis(video_id: str, user_id: str = Depends(require_auth_user)):
    """Delete an analysis and its associated data from cache and Supabase."""
    video = await _get_video_or_404(video_id)
    if user_id != "anonymous" and video.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own analyses")

    await store.delete_analysis(video_id)
    await store.delete_video(video_id)
    _task_status.pop(video_id, None)
    _ws_connections.pop(video_id, None)

    share_ids = _video_share_links.pop(video_id, [])
    for sid in share_ids:
        _share_links.pop(sid, None)
        _share_link_timestamps.pop(sid, None)

    return {"status": "deleted", "video_id": video_id}


@router.get("/reports/{video_id}")
async def get_report(video_id: str):
    video = await _get_video_or_404(video_id)
    analysis = await _get_analysis_or_404(video_id)
    return {
        "report_id": f"report_{video_id}",
        "video": video,
        "analysis": analysis,
        "generated_at": datetime.now().isoformat(),
    }


@router.get("/reports/{video_id}/pdf")
async def download_report_pdf(video_id: str):
    """Download analysis report as PDF."""
    video = await _get_video_or_404(video_id)
    analysis = await _get_analysis_or_404(video_id)
    pdf_bytes = generate_pdf_report(analysis, video)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=neurosim_report_{video_id[:8]}.pdf"},
    )


@router.get("/simulation/{video_id}")
async def get_simulation(video_id: str):
    analysis = await _get_analysis_or_404(video_id)
    return analysis.get("mirofish_simulation", {})


@router.get("/brain-response/{video_id}")
async def get_brain_response(video_id: str):
    analysis = await _get_analysis_or_404(video_id)
    return analysis.get("tribev2_brain_response", {})
