from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from storage_adapter import store
from rate_limiter import check_api_limit, upload_limiter
from pdf_report import generate_pdf_report
from correlation_tracker import CorrelationTracker
from validation_study import ValidationStudy
from bridge_logic import ROI, NeuroSocialBridge
from config import settings
from heuristic_scorer import score_transcript
from routes.upload import process_video
from shared_state import (
    _get_analysis_or_404,
    _get_video_or_404,
    _task_status,
    _ws_connections,
    _share_links,
    _video_share_links,
    _share_link_timestamps,
    _increment_usage,
    _is_premium,
    require_auth_user,
    get_verified_user_id,
)


class FeedbackRequest(BaseModel):
    video_id: str
    actual_views: int
    actual_engagement: float
    would_publish: bool = True


class ValidationSubmitRequest(BaseModel):
    video_id: str
    actual_views: int
    actual_engagement: float
    would_publish: bool = True
    days_after_publish: int = 7


class ScriptAnalysisRequest(BaseModel):
    script: str
    title: Optional[str] = None


router = APIRouter(tags=["analysis"])

_tracker = CorrelationTracker()
_study = ValidationStudy()


@router.post("/api/analyze/script")
async def analyze_script(
    request: Request,
    req: ScriptAnalysisRequest,
    user_id: str = Depends(get_verified_user_id),
):
    """Analyze a script/text instantly using heuristic pipeline.

    No transcription, no video upload. Returns full analysis
    (ROI scores, MiroFish simulation, TRIBE brain response,
    stage-gate, recommendations) in one synchronous call.
    """
    client_ip = request.client.host if request.client else "unknown"
    if not upload_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 5 analyses per 5 minutes.",
        )

    if user_id != "anonymous" and not _is_premium(user_id):
        from shared_state import _usage_tracker
        current_usage = _usage_tracker.get(user_id, 0)
        if current_usage >= settings.premium_max_analyses_free:
            raise HTTPException(
                status_code=403,
                detail=f"Free tier limit reached ({settings.premium_max_analyses_free}/month). Upgrade to Pro for unlimited analyses.",
            )

    text = req.script.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Script text cannot be empty.")
    if len(text) < 50:
        raise HTTPException(
            status_code=400,
            detail="Script too short. Minimum 50 characters for meaningful analysis.",
        )

    script_id = f"script_{uuid.uuid4().hex[:12]}"

    roi_scores = score_transcript(text)
    roi = ROI(
        A5=roi_scores["A5"],
        LO=roi_scores["LO"],
        Area45=roi_scores["Area45"],
        TPJ=roi_scores["TPJ"],
    )

    analysis = await process_video(script_id, "", text, roi)

    analysis["script_title"] = req.title
    analysis["analysis_type"] = "script"
    analysis["source"] = "text_input"

    await store.insert_analysis(script_id, analysis, user_id=user_id)
    await store.insert_video(
        script_id, req.title or "Script Analysis", "analyzed", user_id=user_id
    )

    _increment_usage(user_id)

    return analysis


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


@router.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest, user_id: str = Depends(require_auth_user)):
    """Submit actual video performance data for correlation tracking."""
    analysis = await _get_analysis_or_404(req.video_id)
    predicted_scores = {
        "hook_score": analysis.get("hook_score", 0),
        "viral_potential": analysis.get("viral_potential", 0),
        "success_probability": analysis.get("success_probability", 0),
    }
    _tracker.add_entry(
        video_id=req.video_id,
        predicted_scores=predicted_scores,
        actual_views=req.actual_views,
        actual_engagement=req.actual_engagement,
    )
    return {
        "status": "received",
        "total_entries": _tracker.entry_count(),
    }


@router.get("/api/feedback/correlations")
async def get_correlations():
    """Return current prediction accuracy correlations."""
    return _tracker.get_correlations()


@router.post("/api/validation/submit")
async def submit_validation_data(
    req: ValidationSubmitRequest,
    user_id: str = Depends(require_auth_user),
):
    """Submit actual performance data for the validation study.

    Records the prediction-outcome pair and computes updated correlations.
    Target: 20 users completing the validation loop.
    """
    analysis = await _get_analysis_or_404(req.video_id)
    video = await _get_video_or_404(req.video_id)

    predicted_scores = {
        "hook_score": analysis.get("hook_score", 0),
        "viral_potential": analysis.get("viral_potential", 0),
        "success_probability": analysis.get("success_probability", 0),
    }

    analysis_type = analysis.get("analysis_type", "video")

    entry = _study.add_entry(
        video_id=req.video_id,
        user_id=user_id,
        analysis_type=analysis_type,
        predicted_scores=predicted_scores,
        actual_views=req.actual_views,
        actual_engagement=req.actual_engagement,
        would_publish=req.would_publish,
        days_after_publish=req.days_after_publish,
    )

    correlations = _study.compute_correlations()
    progress = _study.get_study_progress()

    return {
        "status": "received",
        "entry_id": entry.video_id,
        "progress": progress,
        "correlations": correlations,
    }


@router.get("/api/validation/study")
async def get_validation_study():
    """Return validation study progress and correlation results."""
    progress = _study.get_study_progress()
    correlations = _study.compute_correlations()
    benchmarks = _study.get_benchmark_comparison()

    return {
        "progress": progress,
        "correlations": correlations,
        "benchmarks": benchmarks,
    }


@router.get("/api/validation/my-data")
async def get_my_validation_data(user_id: str = Depends(require_auth_user)):
    """Return the authenticated user's validation submissions."""
    entries = _study.get_user_entries(user_id)
    return {"user_id": user_id, "entries": entries, "count": len(entries)}
