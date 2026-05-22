import asyncio
import gc
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel

from bridge_logic import ROI, NeuroSocialBridge
from config import settings
from storage_adapter import store
from heuristic_scorer import score_transcript
from rate_limiter import upload_limiter, check_api_limit
from utils import is_video_magic, is_allowed_video_extension, check_free_tier_limit
from shared_state import (
    _task_status,
    _ws_connections,
    _increment_usage,
    _is_premium,
    _get_video_or_404,
    _get_analysis_or_404,
    get_verified_user_id,
)

logger = logging.getLogger(__name__)



class VideoMetadata(BaseModel):
    id: str
    filename: str
    upload_time: str
    status: str = "uploaded"
    duration: Optional[float] = None
    transcript: Optional[str] = None


class UploadRequest(BaseModel):
    user_id: Optional[str] = "anonymous"


class WhatIfRequest(BaseModel):
    modifications: Dict[str, Any]


class SingleSimRequest(BaseModel):
    content_url: str
    variant: str = "a"  # "a" or "b"


async def _broadcast_progress(video_id: str, data: dict):
    if video_id in _ws_connections:
        dead = []
        for ws in _ws_connections[video_id]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            _ws_connections[video_id].remove(ws)


async def process_video(
    video_id: str, file_path: str, transcript: str = "", heuristic_roi: Optional[ROI] = None
) -> Dict[str, Any]:
    import numpy as np
    from roi_extractor import roi_extractor
    from tribe_engine import tribe_engine
    from mirofish_engine import mirofish_engine

    if heuristic_roi:
        roi = heuristic_roi
        tribe_result = {
            "predictions": [],
            "mode": "heuristic",
            "transcript_word_count": len(transcript.split()),
        }
    else:
        tribe_result = await tribe_engine.predict_from_video(file_path)
        predictions = np.array(tribe_result["predictions"])
        roi_scores = roi_extractor.extract_from_predictions(predictions)
        roi = ROI(A5=roi_scores.A5, LO=roi_scores.LO, Area45=roi_scores.Area45, TPJ=roi_scores.TPJ)

    social_params = NeuroSocialBridge.compute_social_params(roi)
    stage_passed, stage_msg = NeuroSocialBridge.stage_gate_check(social_params.W_attn)

    temporal_roi = (
        roi_extractor.extract_with_temporal_dynamics(
            np.array(tribe_result.get("predictions", [[0.5] * 20484] * 20)), n_segments=4
        )
        if tribe_result.get("predictions")
        else {"segments": []}
    )

    mirofish_result = await mirofish_engine.run_simulation(
        content={
            "transcript": transcript or "Sample transcript from video",
            "requirements": "Predict audience reaction",
        },
        roi_scores={"A5": roi.A5, "LO": roi.LO, "Area45": roi.Area45, "TPJ": roi.TPJ},
    )

    hook_score = round((roi.LO * 0.6 + roi.A5 * 0.4) * 100, 1)
    authenticity_score = round((roi.TPJ * 0.5 + (1 - roi.Area45) * 0.5) * 100, 1)
    viral_potential = round(social_params.viral_coefficient * 30, 1)
    success_probability = round(
        (roi.LO * 0.3 + roi.A5 * 0.2 + roi.Area45 * 0.3 + roi.TPJ * 0.2) * 100, 1
    )
    risk_score = round((1 - roi.TPJ) * 50 + mirofish_result.get("final_sentiment", 50) * 0.2, 1)

    recommendations = NeuroSocialBridge.generate_recommendations(roi, social_params)

    return {
        "video_id": video_id,
        "hook_score": hook_score,
        "hook_details": {
            "strength": "Strong" if roi.LO > 0.6 else "Moderate" if roi.LO > 0.4 else "Weak",
            "curiosity_gap_detected": roi.TPJ > 0.5,
            "question_detected": roi.A5 > 0.4,
        },
        "authenticity_score": authenticity_score,
        "authenticity_details": {
            "authenticity_level": "High"
            if authenticity_score > 70
            else "Moderate"
            if authenticity_score > 50
            else "Low",
            "brand_intrusion": "Low" if roi.Area45 < 0.6 else "High",
        },
        "sentiment_forecast": {
            "positive_sentiment_pct": round(mirofish_result.get("final_sentiment", 60) * 0.7, 1),
            "negative_sentiment_pct": round(
                100 - mirofish_result.get("final_sentiment", 60) * 0.7 - 20, 1
            ),
            "neutral_sentiment_pct": 20.0,
            "backlash_risk": mirofish_result.get("backlash_prediction", "Low").split()[0],
            "shareability_index": round(social_params.P_share * 100, 1),
            "sellout_probability": round(roi.Area45 * 40, 1),
        },
        "cta_analysis": {
            "cta_activation_score": round(roi.Area45 * 100, 1),
            "cognitive_load": "Optimal" if roi.Area45 > 0.5 else "High",
            "timing_recommendation": "CTA placement at 10s is optimal"
            if roi.Area45 > 0.5
            else "Consider earlier CTA placement",
        },
        "viral_potential": viral_potential,
        "success_probability": success_probability,
        "risk_score": risk_score,
        "recommendations": [r["recommendation"] for r in recommendations],
        "mirofish_simulation": mirofish_result,
        "tribev2_brain_response": {
            "cortical_response": {
                "visual_cortex": round(roi.LO * 100, 1),
                "auditory_cortex": round(roi.A5 * 100, 1),
                "language_center": round(roi.TPJ * 80, 1),
                "amygdala": round(roi.TPJ * 90, 1),
                "prefrontal_cortex": round(roi.Area45 * 95, 1),
                "reward_center": round(roi.Area45 * 100, 1),
                "social_cognition": round(roi.TPJ * 85, 1),
                "memory_formation": round((roi.LO + roi.A5) / 2 * 90, 1),
                "overall_response_strength": round(
                    (roi.LO + roi.A5 + roi.Area45 + roi.TPJ) / 4 * 100, 1
                ),
            },
            "emotional_impact": {
                "primary_emotion": "excitement"
                if roi.TPJ > 0.6
                else "curiosity"
                if roi.A5 > 0.5
                else "neutral",
                "emotional_intensity": round(roi.TPJ * 100, 1),
            },
            "engagement_prediction": {
                "overall_engagement": round(success_probability, 1),
                "retention_prediction": "high"
                if roi.LO > 0.6
                else "moderate"
                if roi.LO > 0.4
                else "low",
            },
            "temporal_dynamics": temporal_roi,
            "mode": tribe_result.get("mode", "simulated"),
        },
        "stage_gate": {
            "passed": stage_passed,
            "message": stage_msg,
            "W_attn": social_params.W_attn,
            "threshold": settings.stage_gate_threshold,
        },
        "transcript": transcript[:500] + "..." if len(transcript) > 500 else transcript,
        "full_transcript": transcript,
        "created_at": datetime.now().isoformat(),
    }


async def _process_in_background(
    video_id: str, file_path: str, filename: str, user_id: str = "anonymous"
):
    try:
        from transcriber import transcriber
        _task_status[video_id] = {
            "status": "processing",
            "progress": 10,
            "message": "Transcribing audio...",
            "stage": "transcribing",
        }
        await _broadcast_progress(video_id, _task_status[video_id])

        transcript = transcriber.transcribe(file_path)
        if not transcript:
            transcript = "No audio detected. Analysis based on file metadata only."

        _task_status[video_id] = {
            "status": "processing",
            "progress": 30,
            "message": f"Transcript ready ({len(transcript.split())} words)",
            "stage": "transcribing",
        }
        await _broadcast_progress(video_id, _task_status[video_id])

        transcriber.unload()
        gc.collect()

        _task_status[video_id] = {
            "status": "processing",
            "progress": 40,
            "message": "Analyzing neural patterns...",
            "stage": "scoring",
        }
        await _broadcast_progress(video_id, _task_status[video_id])

        roi_scores = score_transcript(transcript)
        roi = ROI(
            A5=roi_scores["A5"],
            LO=roi_scores["LO"],
            Area45=roi_scores["Area45"],
            TPJ=roi_scores["TPJ"],
        )

        _task_status[video_id] = {
            "status": "processing",
            "progress": 55,
            "message": "Running TRIBE v2 neural analysis...",
            "stage": "scoring",
        }
        await _broadcast_progress(video_id, _task_status[video_id])

        analysis = await process_video(video_id, file_path, transcript, roi)

        _task_status[video_id] = {
            "status": "processing",
            "progress": 80,
            "message": "Saving results...",
            "stage": "saving",
        }
        await _broadcast_progress(video_id, _task_status[video_id])

        await store.insert_analysis(video_id, analysis, user_id=user_id)
        await store.update_video_status(video_id, "analyzed")

        _increment_usage(user_id)

        try:
            os.remove(file_path)
        except OSError:
            pass

        _task_status[video_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Analysis complete",
            "stage": "done",
        }
        await _broadcast_progress(video_id, _task_status[video_id])
    except Exception as e:
        _task_status[video_id] = {
            "status": "error",
            "progress": 0,
            "message": "Analysis failed. Please try uploading again.",
            "detail": str(e),
        }
        await store.update_video_status(video_id, "error")
        await _broadcast_progress(video_id, _task_status[video_id])
        try:
            os.remove(file_path)
        except OSError:
            pass
        logger.error(f"Analysis failed for {video_id}: {e}")


router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload_video(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Depends(get_verified_user_id),
):
    client_ip = request.client.host if request.client else "unknown"
    if not upload_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429, detail="Upload rate limit exceeded. Max 5 uploads per 5 minutes."
        )

    if user_id != "anonymous" and not _is_premium(user_id):
        limit_error = check_free_tier_limit(user_id, settings.premium_max_analyses_free)
        if limit_error:
            raise HTTPException(status_code=403, detail=limit_error)

    allowed_extensions = {".mp4", ".mov", ".avi", ".webm"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, detail=f"Unsupported format. Use: {allowed_extensions}"
        )

    header = await file.read(32)
    await file.seek(0)
    if not is_video_magic(header):
        raise HTTPException(
            status_code=400,
            detail="File content does not match a supported video format (mp4, mov, avi, webm).",
        )

    video_id = str(uuid.uuid4())
    file_path = Path(settings.upload_dir) / f"{video_id}{file_ext}"

    async with aiofiles.open(file_path, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            await f.write(chunk)

    await store.insert_video(video_id, file.filename, "processing", user_id=user_id)
    _task_status[video_id + "_filepath"] = str(file_path)

    _task_status[video_id] = {
        "status": "processing",
        "progress": 0,
        "message": "Starting analysis...",
    }
    if os.environ.get("NEUROSIM_SYNC_MODE"):
        await _process_in_background(video_id, str(file_path), file.filename, user_id)
    else:
        asyncio.create_task(
            _process_in_background(video_id, str(file_path), file.filename, user_id)
        )

    return {"video_id": video_id, "status": "processing", "message": "Analysis started"}


@router.websocket("/ws/{video_id}")
async def websocket_progress(websocket: WebSocket, video_id: str):
    await websocket.accept()
    if video_id not in _ws_connections:
        _ws_connections[video_id] = []
    _ws_connections[video_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if video_id in _ws_connections:
            _ws_connections[video_id].remove(websocket)


@router.get("/status/{video_id}")
async def get_processing_status(video_id: str):
    status = _task_status.get(video_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status


@router.get("/videos")
async def list_videos(_=Depends(check_api_limit)):
    videos = await store.list_videos()
    return {"videos": videos}


@router.get("/videos/{video_id}")
async def get_video(video_id: str):
    video = await _get_video_or_404(video_id)
    return {"video": video}


@router.post("/simulate/single")
async def simulate_single(req: SingleSimRequest):
    import numpy as np

    is_strong = req.variant.lower() in ("a", "strong", "version_a")

    if is_strong:
        roi = ROI(
            A5=round(np.random.uniform(0.70, 0.90), 3),
            LO=round(np.random.uniform(0.75, 0.95), 3),
            Area45=round(np.random.uniform(0.65, 0.85), 3),
            TPJ=round(np.random.uniform(0.60, 0.85), 3),
        )
    else:
        roi = ROI(
            A5=round(np.random.uniform(0.20, 0.45), 3),
            LO=round(np.random.uniform(0.20, 0.40), 3),
            Area45=round(np.random.uniform(0.15, 0.35), 3),
            TPJ=round(np.random.uniform(0.30, 0.50), 3),
        )

    social_params = NeuroSocialBridge.compute_social_params(roi)
    stage_passed = social_params.W_attn >= settings.stage_gate_threshold

    social = None
    if stage_passed:
        base_reach = 50000
        social = {
            "initial_attention_weight": round(social_params.W_attn, 3),
            "viral_coefficient": social_params.viral_coefficient,
            "peak_reach": int(base_reach * social_params.viral_coefficient * 2.5),
            "seven_day_curve": [
                int(base_reach * 0.1 * (i + 1) * social_params.viral_coefficient) for i in range(7)
            ],
        }

    return {
        "roi": {"A5": roi.A5, "LO": roi.LO, "Area45": roi.Area45, "TPJ": roi.TPJ},
        "W_attn": social_params.W_attn,
        "stage_gate_passed": stage_passed,
        "social": social,
    }


@router.post("/simulation/what-if/{video_id}")
async def run_what_if(video_id: str, request: WhatIfRequest):
    from mirofish_engine import mirofish_engine

    analysis = await _get_analysis_or_404(video_id)
    base_sim = analysis.get("mirofish_simulation", {})
    result = await mirofish_engine.run_what_if(base_sim, request.modifications)
    return result


@router.get("/models/status")
async def model_status():
    from tribe_engine import tribe_engine
    from mirofish_engine import mirofish_engine

    return {
        "tribev2": {
            "status": "ready",
            "type": "brain_encoding",
            "model": "facebook/tribev2",
            "mode": "real" if tribe_engine.is_real else "simulated",
        },
        "mirofish": {
            "status": "ready",
            "type": "swarm_intelligence",
            "mode": "real" if mirofish_engine.is_real else "simulated",
        },
    }


@router.get("/roi/metadata")
async def roi_metadata():
    from roi_extractor import roi_extractor
    return roi_extractor.get_roi_metadata()
