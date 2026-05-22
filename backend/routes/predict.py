"""Virality Predictor endpoint — standalone quick-predict flow.

Accepts a video clip (max 15 seconds), runs Gemini 2.5 Flash vision analysis,
merges with heuristic transcript scoring, and returns virality scores without
storing the analysis or running the full MiroFish pipeline.

This is a separate flow from the main upload pipeline — no database writes,
no swarm simulation, no persistent state. Pure prediction.
"""

import hashlib
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from bridge_logic import NeuroSocialBridge
from config import settings
from heuristic_scorer import score_transcript
from rate_limiter import check_predict_limit
from signal_merge import get_analysis_mode, merge_signals
from utils import is_allowed_video_extension, is_video_magic

logger = logging.getLogger(__name__)

router = APIRouter(tags=["predict"])

_MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB for quick predict


def _file_hash_seed(file_path: str) -> str:
    """Return deterministic seed from file bytes for fallback scoring."""
    digest = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _get_video_duration(file_path: str) -> Optional[float]:
    """Get video duration in seconds. Returns None if unable to determine."""
    try:
        import subprocess
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", file_path
            ],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass
    return None


@router.post("/predict")
async def predict_virality(
    request: Request,
    file: UploadFile = File(...),
    _=Depends(check_predict_limit),
):
    """Quick virality prediction for a video clip."""
    from transcriber import transcriber
    from vision_scorer import vision_scorer

    Upload a clip (max 15 seconds recommended). Returns virality score,
    hook score, hold rate, engagement curve, and brain region activations.

    This endpoint does NOT store the analysis or run the full pipeline.
    It's a standalone prediction flow.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"[PREDICT] Request from {client_ip}: {file.filename}")

    # Validate extension
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if not is_allowed_video_extension(file.filename or ""):
        raise HTTPException(
            status_code=400,
            detail="Unsupported format. Use: .mp4, .mov, .avi, .webm"
        )

    # Read and validate magic bytes
    header = await file.read(32)
    await file.seek(0)
    if not is_video_magic(header):
        raise HTTPException(
            status_code=400,
            detail="File does not match a supported video format.",
        )

    # Save to temp file
    video_id = str(uuid.uuid4())
    file_path = Path(settings.upload_dir) / f"predict_{video_id}{file_ext}"
    os.makedirs(settings.upload_dir, exist_ok=True)

    try:
        async with aiofiles.open(file_path, "wb") as f:
            total = 0
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > _MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail="File too large for quick predict (max 100MB)."
                    )
                await f.write(chunk)

        # Check duration (warn if > 15s but don't reject)
        duration = _get_video_duration(str(file_path))
        if duration and duration > settings.vision_max_duration:
            logger.warning(
                f"[PREDICT] Video is {duration:.1f}s (recommended max: {settings.vision_max_duration}s)"
            )

        # Run Whisper transcription (may fail gracefully)
        transcript = ""
        try:
            if transcriber.available:
                transcript = transcriber.transcribe(str(file_path)) or ""
        except Exception as e:
            logger.warning(f"[PREDICT] Transcription failed: {e}")

        # Run heuristic scoring on transcript
        # Always call score_transcript (even for empty strings) so the
        # fallback path returns varied scores with honest labeling.
        heuristic_roi = score_transcript(transcript) if transcript else score_transcript("")

        # Run Gemini vision analysis, with deterministic fallback if unavailable.
        vision_scores = vision_scorer.analyze_video(str(file_path))
        if vision_scores.get("mode") in ("disabled", "error"):
            fallback_duration = int(round(duration)) if duration else settings.vision_max_duration
            vision_scores = vision_scorer.get_fallback_scores(
                duration_seconds=max(1, fallback_duration),
                seed=_file_hash_seed(str(file_path)),
            )

        # Merge signals
        roi = merge_signals(heuristic_roi, vision_scores)
        analysis_mode = get_analysis_mode(bool(transcript), vision_scores.get("mode", ""))

        # Compute derived metrics from merged ROI
        social_params = NeuroSocialBridge.compute_social_params(roi)
        stage_passed, stage_msg = NeuroSocialBridge.stage_gate_check(social_params.W_attn)

        hook_score = round((roi.LO * 0.6 + roi.A5 * 0.4) * 100, 1)
        authenticity_score = round((roi.TPJ * 0.5 + (1 - roi.Area45) * 0.5) * 100, 1)
        viral_potential = round(social_params.viral_coefficient * 30, 1)
        success_probability = round(
            (roi.LO * 0.3 + roi.A5 * 0.2 + roi.Area45 * 0.3 + roi.TPJ * 0.2) * 100, 1
        )

        recommendations = NeuroSocialBridge.generate_recommendations(roi, social_params)
        rec_texts = [r["recommendation"] for r in recommendations]

        # Merge vision recommendations with bridge recommendations
        if vision_scores.get("mode") in ("vision", "fallback"):
            vision_recs = vision_scores.get("recommendations", [])
            rec_texts = vision_recs + rec_texts

        result = {
            "video_id": video_id,
            "analysis_mode": analysis_mode,
            "duration_seconds": round(duration, 1) if duration else None,

            # Virality Predictor scores
            "virality_score": vision_scores.get("virality_score") if vision_scores.get("mode") in ("vision", "fallback") else None,
            "hook_score": hook_score,
            "hook_strength": "Strong" if roi.LO > 0.6 else "Moderate" if roi.LO > 0.4 else "Weak",
            "hold_rate": round(vision_scores.get("hold_rate", 0) * 100, 1) if vision_scores.get("mode") in ("vision", "fallback") else None,
            "peak_hook_timestamp": vision_scores.get("peak_hook_timestamp") if vision_scores.get("mode") in ("vision", "fallback") else None,

            # Engagement curve
            "engagement_curve": vision_scores.get("engagement_curve") if vision_scores.get("mode") in ("vision", "fallback") else None,

            # ROI scores (merged)
            "roi_scores": {
                "A5": roi.A5,
                "LO": roi.LO,
                "Area45": roi.Area45,
                "TPJ": roi.TPJ,
            },

            # Derived metrics
            "authenticity_score": authenticity_score,
            "viral_potential": viral_potential,
            "success_probability": success_probability,
            "stage_gate": {
                "passed": stage_passed,
                "message": stage_msg,
                "W_attn": social_params.W_attn,
            },

            # Brain regions (for 3D visualization)
            "brain_regions": vision_scores.get("brain_regions") if vision_scores.get("mode") in ("vision", "fallback") else None,

            # Recommendations
            "recommendations": rec_texts[:8],  # cap at 8

            # Metadata
            "created_at": datetime.now().isoformat(),
        }

        logger.info(
            f"[PREDICT] Complete: virality={result['virality_score']}, "
            f"hook={hook_score}, mode={analysis_mode}"
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PREDICT] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    finally:
        # Clean up temp file
        try:
            if file_path.exists():
                os.remove(file_path)
        except OSError:
            pass
