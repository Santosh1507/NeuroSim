import json
import re
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from storage_adapter import store
from rate_limiter import check_api_limit, upload_limiter
from pdf_report import generate_pdf_report
from validation_study import ValidationStudy
from youtube_client import extract_video_id, fetch_video_metadata, fetch_youtube_transcript
from benchmark_data import get_benchmark, get_all_cohorts, compare_to_benchmark
from bridge_logic import ROI, NeuroSocialBridge
from config import settings
from heuristic_scorer import score_transcript
from routes.upload import process_video
from utils import check_free_tier_limit
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

# Optional Gemini client — imported once at module load to avoid per-request import overhead
try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    genai = None  # type: ignore
    genai_types = None  # type: ignore
    _GENAI_AVAILABLE = False


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


class YouTubeAnalysisRequest(BaseModel):
    url: str


router = APIRouter(tags=["analysis"])

_study = ValidationStudy()


@router.post("/analyze/script")
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
        limit_error = check_free_tier_limit(user_id, settings.premium_max_analyses_free)
        if limit_error:
            raise HTTPException(status_code=403, detail=limit_error)

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


@router.post("/analyze/youtube")
async def analyze_youtube(
    request: Request,
    req: YouTubeAnalysisRequest,
    user_id: str = Depends(get_verified_user_id),
):
    """Analyze a YouTube video by URL.

    Extracts transcript via youtube-transcript-api, fetches metadata
    via YouTube Data API v3, then runs the full heuristic pipeline.
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

    video_id = extract_video_id(req.url)
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL. Provide a youtube.com or youtu.be link.",
        )

    metadata = await fetch_video_metadata(video_id)
    transcript = await fetch_youtube_transcript(video_id)

    if not transcript:
        raise HTTPException(
            status_code=400,
            detail="No transcript/captions available for this video.",
        )

    roi_scores = score_transcript(transcript)
    roi = ROI(
        A5=roi_scores["A5"],
        LO=roi_scores["LO"],
        Area45=roi_scores["Area45"],
        TPJ=roi_scores["TPJ"],
    )

    analysis_id = f"yt_{video_id}"
    analysis = await process_video(analysis_id, "", transcript, roi)

    analysis["youtube_metadata"] = metadata
    analysis["analysis_type"] = "youtube"
    analysis["source"] = "youtube_url"
    analysis["script_title"] = metadata.get("title")

    await store.insert_analysis(analysis_id, analysis, user_id=user_id)
    await store.insert_video(
        analysis_id, metadata.get("title", video_id), "analyzed", user_id=user_id
    )

    _increment_usage(user_id)

    return analysis


@router.get("/analyses/{video_id}")
async def get_analysis(video_id: str, _=Depends(check_api_limit)):
    return await _get_analysis_or_404(video_id)


@router.delete("/analyses/{video_id}")
async def delete_analysis(video_id: str, user_id: str = Depends(require_auth_user)):
    """Delete an analysis and its associated data from cache and Supabase."""
    if user_id == "anonymous":
        raise HTTPException(status_code=401, detail="Authentication required to delete analyses")
    video = await _get_video_or_404(video_id)
    if video.get("user_id") != user_id:
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


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest, user_id: str = Depends(require_auth_user)):
    """Submit actual video performance data for correlation tracking."""
    analysis = await _get_analysis_or_404(req.video_id)
    predicted_scores = {
        "hook_score": analysis.get("hook_score", 0),
        "viral_potential": analysis.get("viral_potential", 0),
        "success_probability": analysis.get("success_probability", 0),
    }
    analysis_type = analysis.get("analysis_type", "video")

    _study.add_entry(
        video_id=req.video_id,
        user_id=user_id,
        analysis_type=analysis_type,
        predicted_scores=predicted_scores,
        actual_views=req.actual_views,
        actual_engagement=req.actual_engagement,
        would_publish=req.would_publish,
        days_after_publish=7,
    )
    return {
        "status": "received",
        "total_entries": _study.get_study_progress()["total_entries"],
    }


@router.get("/feedback/correlations")
async def get_correlations():
    """Return current prediction accuracy correlations."""
    return _study.compute_correlations()


@router.post("/validation/submit")
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


@router.get("/validation/study")
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


@router.get("/validation/my-data")
async def get_my_validation_data(user_id: str = Depends(require_auth_user)):
    """Return the authenticated user's validation submissions."""
    entries = _study.get_user_entries(user_id)
    return {"user_id": user_id, "entries": entries, "count": len(entries)}


@router.get("/benchmarks")
async def get_benchmarks():
    """Return all available benchmark cohorts."""
    return {"cohorts": get_all_cohorts()}


class BenchmarkCompareRequest(BaseModel):
    video_id: str
    cohort: str = "all"


@router.post("/benchmarks/compare")
async def compare_with_benchmark(req: BenchmarkCompareRequest):
    """Compare analysis scores against a benchmark cohort."""
    analysis = await _get_analysis_or_404(req.video_id)
    user_scores = {
        "hook_score": analysis.get("hook_score", 0),
        "viral_potential": analysis.get("viral_potential", 0),
        "success_probability": analysis.get("success_probability", 0),
        "authenticity_score": analysis.get("authenticity_score", 0),
        "risk_score": analysis.get("risk_score", 0),
    }

    comparison = compare_to_benchmark(user_scores, req.cohort)
    benchmark = get_benchmark(req.cohort)

    return {
        "video_id": req.video_id,
        "cohort": benchmark["label"],
        "cohort_n": benchmark["n"],
        "comparison": comparison,
    }


class ScriptRewriteRequest(BaseModel):
    video_id: Optional[str] = None
    script: Optional[str] = None
    dimension: str
    additional_instructions: Optional[str] = None


@router.post("/analyze/rewrite")
async def rewrite_script(
    req: ScriptRewriteRequest,
    user_id: str = Depends(get_verified_user_id),
):
    """Rewrite a script to boost a specific dimension using Gemini 2.5 Flash."""
    original_text = ""
    if req.video_id:
        try:
            analysis = await _get_analysis_or_404(req.video_id)
            original_text = analysis.get("full_transcript") or analysis.get("transcript") or ""
            if original_text.endswith("...") and not analysis.get("full_transcript"):
                original_text = original_text[:-3]
        except Exception:
            pass

    if not original_text and req.script:
        original_text = req.script.strip()

    if not original_text:
        raise HTTPException(status_code=400, detail="No script content found or provided.")

    dimension_lower = req.dimension.lower()
    if dimension_lower not in ["hook", "authenticity", "cta"]:
        raise HTTPException(status_code=400, detail="Invalid dimension. Must be 'hook', 'authenticity', or 'cta'.")

    if dimension_lower == "hook":
        dimension_desc = "Hook (opening 3 seconds of the video). Instantly grab attention, spark deep curiosity, start in media res, or introduce a massive question/dilemma."
    elif dimension_lower == "authenticity":
        dimension_desc = "Authenticity (conversational, natural, relatable, human tone). Remove overly corporate, formal, or sales-heavy expressions. Use conversational pauses, natural transitions, and relatable analogies."
    else:
        dimension_desc = "CTA (Call-to-Action). Make the final action clear, low-friction, extremely rewarding, and seamlessly integrated into the narrative flow of the video."

    prompt = f"""You are a world-class viral video script doctor. Your goal is to rewrite the provided script to boost the target ROI metric: {dimension_desc}.

Original Script:
{original_text}

Additional instructions/preferences:
{req.additional_instructions or "None"}

Rewrite the script to dramatically improve the selected metric while preserving the core message, key value propositions, and general length of the original.

You MUST return ONLY a valid JSON object matching the following structure exactly:
{{
  "rewritten_script": "The complete rewritten script text",
  "explanation": "A concise explanation of the changes made and why they boost the target metric",
  "estimated_improvements": {{
    "before_score": 50,
    "after_score": 85,
    "rationale": "Explanation of score improvement"
  }}
}}
"""

    api_key = settings.gemini_api_key
    model = settings.gemini_model

    if api_key and _GENAI_AVAILABLE and genai is not None:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=[prompt],
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            text = response.text.strip()
            if text.startswith("```"):
                text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
                text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
                text = text.strip()

            data = json.loads(text)
            return data

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemini rewrite failed: {str(e)}")
    else:
        simulated_rewrites = {
            "hook": {
                "rewritten_script": f"🚨 Stop scrolling! If you're still doing manual video editing, you are literally burning cash. Let me show you how... {original_text}",
                "explanation": "Added a high-impact pattern interrupt ('Stop scrolling!') and an immediate pain point ('burning cash') in the first 3 seconds to maximize attention hold.",
                "estimated_improvements": {
                    "before_score": 50,
                    "after_score": 90,
                    "rationale": "Direct pain-point framing combined with an opening hook pattern interrupt increases the opening retention score."
                }
            },
            "authenticity": {
                "rewritten_script": f"Honestly, I was skeptical about this too at first. But here is the raw, unedited truth: {original_text}",
                "explanation": "Added peer-to-peer vulnerability ('Honestly, I was skeptical') and unvarnished honesty signals to break the commercial barrier and build trust.",
                "estimated_improvements": {
                    "before_score": 60,
                    "after_score": 88,
                    "rationale": "High peer trust reduces perceived marketing intrusion and spikes social engagement metrics."
                }
            },
            "cta": {
                "rewritten_script": f"{original_text} So, if you want to stop wasting hours every single week, just tap the link below. It takes 2 minutes and is completely free.",
                "explanation": "Shifted a generic call-to-action into a frictionless value proposition focusing on urgent time-saving benefits and ease-of-action.",
                "estimated_improvements": {
                    "before_score": 45,
                    "after_score": 85,
                    "rationale": "Low cognitive friction combined with direct benefit-aligned actions guarantees higher CTR."
                }
            }
        }
        return simulated_rewrites.get(dimension_lower, simulated_rewrites["hook"])

