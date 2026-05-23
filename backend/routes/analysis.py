import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from storage_adapter import store, _analyses_cache
from rate_limiter import check_api_limit, upload_limiter
from pdf_report import generate_pdf_report
from dataclasses import asdict
from validation_study import ValidationStudy
from youtube_client import extract_video_id, fetch_video_metadata, fetch_youtube_transcript
from benchmark_data import get_benchmark, get_all_cohorts, compare_to_benchmark
from bridge_logic import ROI, NeuroSocialBridge
from config import settings
from heuristic_scorer import score_transcript
from llm_scorer import LLMScorer
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


logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])

_study = ValidationStudy(store=store)
_llm_scorer = LLMScorer(api_key=settings.gemini_api_key, model=settings.gemini_model)


async def sync_validation_to_store():
    """Sync local validation entries to Supabase store at startup."""
    if _study.store is None:
        return
    synced = 0
    for entry in _study._entries:
        try:
            await _study.store.insert_validation_entry(asdict(entry))
            synced += 1
        except Exception:
            pass
    if synced:
        logger.info(f"ValidationStudy: synced {synced} entries to store")


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

    is_pro = _is_premium(user_id)
    if is_pro and _llm_scorer.enabled:
        llm_result = _llm_scorer.score_transcript(text)
        if llm_result.get("mode") == "llm":
            analysis["llm_scored"] = True
            analysis["llm_scores"] = {
                "A5": llm_result["A5"],
                "LO": llm_result["LO"],
                "Area45": llm_result["Area45"],
                "TPJ": llm_result["TPJ"],
                "rationale": llm_result.get("rationale", ""),
            }
            analysis["llm_cortical_response"] = {
                "visual_cortex": round(llm_result["LO"] * 100, 1),
                "auditory_cortex": round(llm_result["A5"] * 100, 1),
                "language_center": round(llm_result["TPJ"] * 80, 1),
                "amygdala": round(llm_result["TPJ"] * 90, 1),
                "prefrontal_cortex": round(llm_result["Area45"] * 95, 1),
                "reward_center": round(llm_result["Area45"] * 100, 1),
                "social_cognition": round(llm_result["TPJ"] * 85, 1),
                "memory_formation": round((llm_result["LO"] + llm_result["A5"]) / 2 * 90, 1),
                "overall_response_strength": round(
                    (llm_result["LO"] + llm_result["A5"] + llm_result["Area45"] + llm_result["TPJ"]) / 4 * 100, 1
                ),
            }
            analysis["llm_engagement_prediction"] = {
                "overall_engagement": round(
                    (llm_result["LO"] * 0.3 + llm_result["A5"] * 0.2 + llm_result["Area45"] * 0.3 + llm_result["TPJ"] * 0.2) * 100, 1
                ),
                "retention_prediction": "high" if llm_result["LO"] > 0.6 else "moderate" if llm_result["LO"] > 0.4 else "low",
            }

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

    is_pro = _is_premium(user_id)
    if is_pro and _llm_scorer.enabled:
        llm_result = _llm_scorer.score_transcript(transcript)
        if llm_result.get("mode") == "llm":
            analysis["llm_scored"] = True
            analysis["llm_scores"] = {
                "A5": llm_result["A5"],
                "LO": llm_result["LO"],
                "Area45": llm_result["Area45"],
                "TPJ": llm_result["TPJ"],
                "rationale": llm_result.get("rationale", ""),
            }
            analysis["llm_cortical_response"] = {
                "visual_cortex": round(llm_result["LO"] * 100, 1),
                "auditory_cortex": round(llm_result["A5"] * 100, 1),
                "language_center": round(llm_result["TPJ"] * 80, 1),
                "amygdala": round(llm_result["TPJ"] * 90, 1),
                "prefrontal_cortex": round(llm_result["Area45"] * 95, 1),
                "reward_center": round(llm_result["Area45"] * 100, 1),
                "social_cognition": round(llm_result["TPJ"] * 85, 1),
                "memory_formation": round((llm_result["LO"] + llm_result["A5"]) / 2 * 90, 1),
                "overall_response_strength": round(
                    (llm_result["LO"] + llm_result["A5"] + llm_result["Area45"] + llm_result["TPJ"]) / 4 * 100, 1
                ),
            }
            analysis["llm_engagement_prediction"] = {
                "overall_engagement": round(
                    (llm_result["LO"] * 0.3 + llm_result["A5"] * 0.2 + llm_result["Area45"] * 0.3 + llm_result["TPJ"] * 0.2) * 100, 1
                ),
                "retention_prediction": "high" if llm_result["LO"] > 0.6 else "moderate" if llm_result["LO"] > 0.4 else "low",
            }

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

    filename = video.get("filename", video_id)
    logger.info(f"User {user_id} deleting analysis {video_id} (file: {filename})")

    await store.delete_analysis(video_id)
    await store.delete_video(video_id)
    _task_status.pop(video_id, None)
    _ws_connections.pop(video_id, None)

    share_ids = _video_share_links.pop(video_id, [])
    for sid in share_ids:
        _share_links.pop(sid, None)
        _share_link_timestamps.pop(sid, None)

    logger.info(f"Analysis {video_id} deleted by user {user_id} — cleaned {len(share_ids)} share links")

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
async def download_report_pdf(
    video_id: str,
    user_id: str = Depends(get_verified_user_id),
):
    """Download analysis report as PDF (Pro tier feature)."""
    if not _is_premium(user_id):
        raise HTTPException(
            status_code=403,
            detail="PDF reports are a Pro feature. Upgrade to download.",
        )
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


@router.get("/analysis-response/{video_id}")
async def get_analysis_response(video_id: str):
    analysis = await _get_analysis_or_404(video_id)
    return analysis.get("analysis_response", {})


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

    await _study.add_entry(
        video_id=req.video_id,
        user_id=user_id,
        analysis_type=analysis_type,
        predicted_scores=predicted_scores,
        actual_views=req.actual_views,
        actual_engagement=req.actual_engagement,
        would_publish=req.would_publish,
        days_after_publish=7,
    )
    progress = _study.get_study_progress()
    return {
        "status": "received",
        "total_entries": progress["total_entries"],
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

    entry = await _study.add_entry(
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
    """Return validation study progress, correlation results, and prediction accuracy."""
    progress = _study.get_study_progress()
    correlations = _study.compute_correlations()
    benchmarks = _study.get_benchmark_comparison()
    accuracy = _study.compute_accuracy()

    return {
        "progress": progress,
        "correlations": correlations,
        "benchmarks": benchmarks,
        "accuracy": accuracy,
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


@router.get("/analyses/{video_id}/compare")
async def compare_scorers(video_id: str, _=Depends(check_api_limit)):
    """Return heuristic vs LLM scores side-by-side for comparison."""
    analysis = await _get_analysis_or_404(video_id)
    text = analysis.get("full_transcript") or analysis.get("transcript") or ""
    if not text:
        raise HTTPException(status_code=400, detail="No transcript available for comparison.")

    heuristic = score_transcript(text)
    llm_result = _llm_scorer.score_transcript(text) if _llm_scorer.enabled else {"mode": "disabled"}

    dims = ["A5", "LO", "Area45", "TPJ"]
    deltas = {}
    for d in dims:
        h = heuristic.get(d, 0)
        l = llm_result.get(d, 0) if llm_result.get("mode") == "llm" else None
        if l is not None:
            deltas[d] = round(l - h, 3)

    return {
        "video_id": video_id,
        "transcript_word_count": len(text.split()),
        "heuristic": {d: heuristic.get(d, 0) for d in dims},
        "llm": {d: llm_result.get(d, 0) for d in dims} if llm_result.get("mode") == "llm" else None,
        "deltas": deltas if deltas else None,
        "llm_mode": llm_result.get("mode", "disabled"),
        "llm_rationale": llm_result.get("rationale") if llm_result.get("mode") == "llm" else None,
    }


class ScriptRewriteRequest(BaseModel):
    video_id: Optional[str] = None
    script: Optional[str] = None
    dimension: str
    additional_instructions: Optional[str] = None


@router.post("/analyze/rewrite")
async def rewrite_script(
    req: ScriptRewriteRequest,
    _=Depends(check_api_limit),
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


@router.get("/validation/pending-followups")
async def get_pending_validation_followups():
    """Return analyses 7+ days old that still lack validation data.

    Used by a scheduled cron job to trigger email follow-ups asking users
    to submit their actual views/engagement.
    """
    from datetime import timedelta, timezone

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)
    validated_video_ids = {e.video_id for e in _study._entries}
    pending = []

    for vid, analysis in _analyses_cache.items():
        if not isinstance(analysis, dict):
            continue
        created = analysis.get("created_at")
        if not created:
            continue
        try:
            created_dt = datetime.fromisoformat(created)
        except (ValueError, TypeError):
            continue
        if created_dt.replace(tzinfo=timezone.utc) > cutoff:
            continue
        if vid in validated_video_ids:
            continue
        pending.append({
            "video_id": vid,
            "user_id": analysis.get("user_id", "unknown"),
            "analyzed_at": created,
            "hook_score": analysis.get("hook_score"),
            "success_probability": analysis.get("success_probability"),
        })

    return {
        "pending_count": len(pending),
        "cutoff_date": cutoff.isoformat(),
        "pending": pending,
    }

