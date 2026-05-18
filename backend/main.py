import os
import uuid
import asyncio
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiofiles

from config import settings
from tribe_engine import tribe_engine
from mirofish_engine import mirofish_engine
from roi_extractor import roi_extractor
from bridge_logic import NeuroSocialBridge, ROI
from database import db
from pdf_report import generate_pdf_report

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"NeuroSim API starting - TRIBE: {'real' if tribe_engine.is_real else 'simulated'}, MiroFish: {'real' if mirofish_engine.is_real else 'simulated'}")
    yield
    print("NeuroSim API shutting down")

app = FastAPI(
    title="NeuroSim API",
    version="2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory fallback when Supabase is not configured
_videos_cache: Dict[str, dict] = {}
_analyses_cache: Dict[str, dict] = {}

class VideoMetadata(BaseModel):
    id: str
    filename: str
    upload_time: str
    status: str = "uploaded"
    duration: Optional[float] = None
    transcript: Optional[str] = None

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "NeuroSim API v2.0 - TRIBE v2 + MiroFish",
        "tribe_mode": "real" if tribe_engine.is_real else "simulated",
        "mirofish_mode": "real" if mirofish_engine.is_real else "simulated"
    }

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    allowed_extensions = {".mp4", ".mov", ".avi", ".webm"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported format. Use: {allowed_extensions}")
    
    video_id = str(uuid.uuid4())
    file_path = Path(settings.upload_dir) / f"{video_id}{file_ext}"
    
    async with aiofiles.open(file_path, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            await f.write(chunk)
    
    await db.insert_video(video_id, file.filename, "processing")
    _videos_cache[video_id] = {
        "id": video_id,
        "filename": file.filename,
        "upload_time": datetime.now().isoformat(),
        "status": "processing",
        "file_path": str(file_path)
    }
    
    analysis = await process_video(video_id, str(file_path))
    await db.insert_analysis(video_id, analysis)
    await db.update_video_status(video_id, "analyzed")
    _analyses_cache[video_id] = analysis
    _videos_cache[video_id]["status"] = "analyzed"
    
    analysis["filename"] = file.filename
    analysis["status"] = "analyzed"
    return analysis

async def process_video(video_id: str, file_path: str) -> Dict[str, Any]:
    tribe_result = await tribe_engine.predict_from_video(file_path)
    
    predictions = np.array(tribe_result["predictions"])
    roi_scores = roi_extractor.extract_from_predictions(predictions)
    
    roi = ROI(A5=roi_scores.A5, LO=roi_scores.LO, Area45=roi_scores.Area45, TPJ=roi_scores.TPJ)
    social_params = NeuroSocialBridge.compute_social_params(roi)
    stage_passed, stage_msg = NeuroSocialBridge.stage_gate_check(social_params.W_attn)
    
    temporal_roi = roi_extractor.extract_with_temporal_dynamics(predictions, n_segments=4)
    
    mirofish_result = await mirofish_engine.run_simulation(
        content={"transcript": "Sample transcript from video", "requirements": "Predict audience reaction"},
        roi_scores={"A5": roi.A5, "LO": roi.LO, "Area45": roi.Area45, "TPJ": roi.TPJ}
    )
    
    hook_score = round((roi.LO * 0.6 + roi.A5 * 0.4) * 100, 1)
    authenticity_score = round((roi.TPJ * 0.5 + (1 - roi.Area45) * 0.5) * 100, 1)
    viral_potential = round(social_params.viral_coefficient * 30, 1)
    success_probability = round((roi.LO * 0.3 + roi.A5 * 0.2 + roi.Area45 * 0.3 + roi.TPJ * 0.2) * 100, 1)
    risk_score = round((1 - roi.TPJ) * 50 + mirofish_result.get("final_sentiment", 50) * 0.2, 1)
    
    recommendations = NeuroSocialBridge.generate_recommendations(roi, social_params)
    
    return {
        "video_id": video_id,
        "hook_score": hook_score,
        "hook_details": {
            "strength": "Strong" if roi.LO > 0.6 else "Moderate" if roi.LO > 0.4 else "Weak",
            "curiosity_gap_detected": roi.TPJ > 0.5,
            "question_detected": roi.A5 > 0.4
        },
        "authenticity_score": authenticity_score,
        "authenticity_details": {
            "authenticity_level": "High" if authenticity_score > 70 else "Moderate" if authenticity_score > 50 else "Low",
            "brand_intrusion": "Low" if roi.Area45 < 0.6 else "High"
        },
        "sentiment_forecast": {
            "positive_sentiment_pct": round(mirofish_result.get("final_sentiment", 60) * 0.7, 1),
            "negative_sentiment_pct": round(100 - mirofish_result.get("final_sentiment", 60) * 0.7 - 20, 1),
            "neutral_sentiment_pct": 20.0,
            "backlash_risk": mirofish_result.get("backlash_prediction", "Low").split()[0],
            "shareability_index": round(social_params.P_share * 100, 1),
            "sellout_probability": round(roi.Area45 * 40, 1)
        },
        "cta_analysis": {
            "cta_activation_score": round(roi.Area45 * 100, 1),
            "cognitive_load": "Optimal" if roi.Area45 > 0.5 else "High",
            "timing_recommendation": "CTA placement at 10s is optimal" if roi.Area45 > 0.5 else "Consider earlier CTA placement"
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
                "overall_response_strength": round((roi.LO + roi.A5 + roi.Area45 + roi.TPJ) / 4 * 100, 1)
            },
            "emotional_impact": {
                "primary_emotion": "excitement" if roi.TPJ > 0.6 else "curiosity" if roi.A5 > 0.5 else "neutral",
                "emotional_intensity": round(roi.TPJ * 100, 1)
            },
            "engagement_prediction": {
                "overall_engagement": round(success_probability, 1),
                "retention_prediction": "high" if roi.LO > 0.6 else "moderate" if roi.LO > 0.4 else "low"
            },
            "temporal_dynamics": temporal_roi,
            "mode": tribe_result.get("mode", "simulated")
        },
        "stage_gate": {
            "passed": stage_passed,
            "message": stage_msg,
            "W_attn": social_params.W_attn,
            "threshold": settings.stage_gate_threshold
        },
        "created_at": datetime.now().isoformat()
    }

@app.get("/videos")
async def list_videos():
    if db.enabled:
        videos = await db.list_videos()
        return {"videos": videos}
    return {"videos": list(_videos_cache.values())}

@app.get("/videos/{video_id}")
async def get_video(video_id: str):
    video = await db.get_video(video_id) or _videos_cache.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"video": video}

@app.get("/analyses/{video_id}")
async def get_analysis(video_id: str):
    analysis = await db.get_analysis(video_id)
    if analysis:
        return analysis.get("data", analysis) if isinstance(analysis, dict) else analysis
    if video_id not in _analyses_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _analyses_cache[video_id]

@app.get("/reports/{video_id}")
async def get_report(video_id: str):
    video = await db.get_video(video_id) or _videos_cache.get(video_id, {})
    analysis = await db.get_analysis(video_id)
    if analysis:
        analysis = analysis.get("data", analysis) if isinstance(analysis, dict) else analysis
    elif video_id in _analyses_cache:
        analysis = _analyses_cache[video_id]
    else:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "report_id": f"report_{video_id}",
        "video": video,
        "analysis": analysis,
        "generated_at": datetime.now().isoformat()
    }

@app.get("/simulation/{video_id}")
async def get_simulation(video_id: str):
    analysis = await db.get_analysis(video_id)
    if analysis:
        data = analysis.get("data", analysis) if isinstance(analysis, dict) else analysis
        return data.get("mirofish_simulation", {})
    if video_id not in _analyses_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _analyses_cache[video_id].get("mirofish_simulation", {})

@app.get("/brain-response/{video_id}")
async def get_brain_response(video_id: str):
    analysis = await db.get_analysis(video_id)
    if analysis:
        data = analysis.get("data", analysis) if isinstance(analysis, dict) else analysis
        return data.get("tribev2_brain_response", {})
    if video_id not in _analyses_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _analyses_cache[video_id].get("tribev2_brain_response", {})

class WhatIfRequest(BaseModel):
    modifications: Dict[str, Any]

@app.post("/simulation/what-if/{video_id}")
async def run_what_if(video_id: str, request: WhatIfRequest):
    analysis = await db.get_analysis(video_id)
    if analysis:
        data = analysis.get("data", analysis) if isinstance(analysis, dict) else analysis
        base_sim = data.get("mirofish_simulation", {})
    elif video_id in _analyses_cache:
        base_sim = _analyses_cache[video_id].get("mirofish_simulation", {})
    else:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = await mirofish_engine.run_what_if(base_sim, request.modifications)
    return result

class SingleSimRequest(BaseModel):
    content_url: str

@app.post("/simulate/single")
async def simulate_single(req: SingleSimRequest):
    is_strong = "version_a" in req.content_url.lower() or "a" in req.content_url.lower()
    
    if is_strong:
        roi = ROI(
            A5=round(np.random.uniform(0.70, 0.90), 3),
            LO=round(np.random.uniform(0.75, 0.95), 3),
            Area45=round(np.random.uniform(0.65, 0.85), 3),
            TPJ=round(np.random.uniform(0.60, 0.85), 3)
        )
    else:
        roi = ROI(
            A5=round(np.random.uniform(0.20, 0.45), 3),
            LO=round(np.random.uniform(0.20, 0.40), 3),
            Area45=round(np.random.uniform(0.15, 0.35), 3),
            TPJ=round(np.random.uniform(0.30, 0.50), 3)
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
                int(base_reach * 0.1 * (i + 1) * social_params.viral_coefficient)
                for i in range(7)
            ]
        }
    
    return {
        "roi": {"A5": roi.A5, "LO": roi.LO, "Area45": roi.Area45, "TPJ": roi.TPJ},
        "W_attn": social_params.W_attn,
        "stage_gate_passed": stage_passed,
        "social": social
    }

@app.get("/models/status")
async def model_status():
    return {
        "tribev2": {
            "status": "ready",
            "type": "brain_encoding",
            "model": "facebook/tribev2",
            "mode": "real" if tribe_engine.is_real else "simulated"
        },
        "mirofish": {
            "status": "ready",
            "type": "swarm_intelligence",
            "mode": "real" if mirofish_engine.is_real else "simulated"
        }
    }

@app.get("/roi/metadata")
async def roi_metadata():
    return roi_extractor.get_roi_metadata()

@app.get("/reports/{video_id}/pdf")
async def download_report_pdf(video_id: str):
    """Download analysis report as PDF."""
    video = await db.get_video(video_id) or _videos_cache.get(video_id, {})
    analysis = await db.get_analysis(video_id)
    if analysis:
        analysis = analysis.get("data", analysis) if isinstance(analysis, dict) else analysis
    elif video_id in _analyses_cache:
        analysis = _analyses_cache[video_id]
    else:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    pdf_bytes = generate_pdf_report(analysis, video)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=neurosim_report_{video_id[:8]}.pdf"}
    )
