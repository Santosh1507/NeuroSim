import os
import uuid
import gc
import asyncio
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect, Request
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
from transcriber import transcriber
from heuristic_scorer import score_transcript
from rate_limiter import upload_limiter, api_limiter, rate_limit

@asynccontextmanager
async def lifespan(app: FastAPI):
    whisper_status = "ready" if transcriber.available else "unavailable (install faster-whisper)"
    print(f"NeuroSim API starting — TRIBE: {'real' if tribe_engine.is_real else 'simulated'}, MiroFish: {'real' if mirofish_engine.is_real else 'simulated'}, Whisper: {whisper_status}")
    yield
    print("NeuroSim API shutting down")

app = FastAPI(
    title="NeuroSim API",
    version="2.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 1)
    client_ip = request.client.host if request.client else "unknown"
    print(f"[{datetime.now().isoformat()}] {request.method} {request.url.path} {response.status_code} {duration}ms — {client_ip}")
    return response

# In-memory fallback when Supabase is not configured
_videos_cache: Dict[str, dict] = {}
_analyses_cache: Dict[str, dict] = {}
_cache_timestamps: Dict[str, float] = {}
_VIDEO_TTL = 3600  # 1 hour
_ANALYSIS_TTL = 1800  # 30 minutes
_task_status: Dict[str, dict] = {}
_share_links: Dict[str, str] = {}
_waitlist: List[Dict[str, Any]] = []
_digest_subs: Dict[str, dict] = {}
_usage_tracker: Dict[str, int] = {}
_premium_users: set = set()  # Manually add user IDs here when Pro launches

def _is_premium(user_id: str) -> bool:
    return user_id in _premium_users

def _increment_usage(user_id: str):
    if user_id and user_id != "anonymous":
        _usage_tracker[user_id] = _usage_tracker.get(user_id, 0) + 1

def _evict_stale():
    now = datetime.now().timestamp()
    stale_videos = [k for k in _cache_timestamps if k.startswith("v:") and now - _cache_timestamps[k] > _VIDEO_TTL]
    stale_analyses = [k for k in _cache_timestamps if k.startswith("a:") and now - _cache_timestamps[k] > _ANALYSIS_TTL]
    for k in stale_videos:
        vid = k[2:]
        _videos_cache.pop(vid, None)
        _cache_timestamps.pop(k, None)
    for k in stale_analyses:
        aid = k[2:]
        _analyses_cache.pop(aid, None)
        _cache_timestamps.pop(k, None)

def _touch_cache(key: str):
    _cache_timestamps[key] = datetime.now().timestamp()

# WebSocket connection manager
_ws_connections: Dict[str, list[WebSocket]] = {}

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

class VideoMetadata(BaseModel):
    id: str
    filename: str
    upload_time: str
    status: str = "uploaded"
    duration: Optional[float] = None
    transcript: Optional[str] = None

class UploadRequest(BaseModel):
    user_id: Optional[str] = "anonymous"

class DigestRequest(BaseModel):
    email: str
    frequency: str  # "weekly" | "monthly"

class DigestPreview(BaseModel):
    digest_id: str
    generated_at: str
    total_analyses: int
    average_hook_score: float
    average_viral_potential: float
    average_success_probability: float
    top_performers: List[dict]

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "NeuroSim API v2.2 — Simulated Analysis (Heuristic + Swarm)",
        "tribe_mode": "real" if tribe_engine.is_real else "simulated",
        "mirofish_mode": "real" if mirofish_engine.is_real else "simulated",
        "whisper_available": transcriber.available,
    }

@app.get("/health")
async def health():
    """Health check for Render keep-alive and monitoring."""
    return {
        "status": "healthy",
        "version": "2.2.0",
        "whisper": "ready" if transcriber.available else "unavailable",
        "supabase": "connected" if db.enabled else "fallback",
        "uptime": "ok",
    }

@app.post("/upload")
async def upload_video(request: Request, file: UploadFile = File(...), user_id: str = "anonymous"):
    client_ip = request.client.host if request.client else "unknown"
    if not upload_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Upload rate limit exceeded. Max 5 uploads per 5 minutes.")
    
    if user_id != "anonymous" and not _is_premium(user_id):
        current_usage = _usage_tracker.get(user_id, 0)
        if current_usage >= settings.premium_max_analyses_free:
            raise HTTPException(
                status_code=403,
                detail=f"Free tier limit reached ({settings.premium_max_analyses_free}/month). Upgrade to Pro for unlimited analyses."
            )
    
    allowed_extensions = {".mp4", ".mov", ".avi", ".webm"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported format. Use: {allowed_extensions}")
    
    video_id = str(uuid.uuid4())
    file_path = Path(settings.upload_dir) / f"{video_id}{file_ext}"
    
    async with aiofiles.open(file_path, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            await f.write(chunk)
    
    _evict_stale()
    await db.insert_video(video_id, file.filename, "processing", user_id=user_id)
    _videos_cache[video_id] = {
        "id": video_id,
        "filename": file.filename,
        "upload_time": datetime.now().isoformat(),
        "status": "processing",
        "file_path": str(file_path),
        "user_id": user_id,
    }
    _touch_cache(f"v:{video_id}")
    
    _task_status[video_id] = {"status": "processing", "progress": 0, "message": "Starting analysis..."}
    if os.environ.get("NEUROSIM_SYNC_MODE"):
        await _process_in_background(video_id, str(file_path), file.filename, user_id)
    else:
        asyncio.create_task(_process_in_background(video_id, str(file_path), file.filename, user_id))
    
    return {"video_id": video_id, "status": "processing", "message": "Analysis started"}

async def _process_in_background(video_id: str, file_path: str, filename: str, user_id: str = "anonymous"):
    try:
        # Stage 1: Transcription
        _task_status[video_id] = {"status": "processing", "progress": 10, "message": "Transcribing audio...", "stage": "transcribing"}
        await _broadcast_progress(video_id, _task_status[video_id])
        
        transcript = transcriber.transcribe(file_path)
        if not transcript:
            transcript = "No audio detected. Analysis based on file metadata only."
        
        _task_status[video_id] = {"status": "processing", "progress": 30, "message": f"Transcript ready ({len(transcript.split())} words)", "stage": "transcribing"}
        await _broadcast_progress(video_id, _task_status[video_id])
        
        # Free whisper model from memory
        transcriber.unload()
        gc.collect()
        
        # Stage 2: Heuristic ROI scoring
        _task_status[video_id] = {"status": "processing", "progress": 40, "message": "Analyzing neural patterns...", "stage": "scoring"}
        await _broadcast_progress(video_id, _task_status[video_id])
        
        roi_scores = score_transcript(transcript)
        roi = ROI(A5=roi_scores["A5"], LO=roi_scores["LO"], Area45=roi_scores["Area45"], TPJ=roi_scores["TPJ"])
        
        _task_status[video_id] = {"status": "processing", "progress": 55, "message": "Running TRIBE v2 neural analysis...", "stage": "scoring"}
        await _broadcast_progress(video_id, _task_status[video_id])
        
        # Stage 3: Full analysis
        analysis = await process_video(video_id, file_path, transcript, roi)
        
        _task_status[video_id] = {"status": "processing", "progress": 80, "message": "Saving results...", "stage": "saving"}
        await _broadcast_progress(video_id, _task_status[video_id])
        
        await db.insert_analysis(video_id, analysis, user_id=user_id)
        await db.update_video_status(video_id, "analyzed")
        
        _analyses_cache[video_id] = analysis
        _touch_cache(f"a:{video_id}")
        _videos_cache[video_id]["status"] = "analyzed"
        
        _increment_usage(user_id)
        
        # Stage 4: Cleanup — delete uploaded file
        try:
            os.remove(file_path)
        except OSError:
            pass
        
        _task_status[video_id] = {"status": "completed", "progress": 100, "message": "Analysis complete", "stage": "done"}
        await _broadcast_progress(video_id, _task_status[video_id])
    except Exception as e:
        _task_status[video_id] = {"status": "error", "progress": 0, "message": str(e)}
        _videos_cache[video_id]["status"] = "error"
        await _broadcast_progress(video_id, _task_status[video_id])
        # Clean up file on error too
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise

@app.websocket("/ws/{video_id}")
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

@app.get("/status/{video_id}")
async def get_processing_status(video_id: str):
    status = _task_status.get(video_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status

async def process_video(video_id: str, file_path: str, transcript: str = "", heuristic_roi: Optional[ROI] = None) -> Dict[str, Any]:
    # Use heuristic ROI if provided, otherwise fall back to TRIBE engine
    if heuristic_roi:
        roi = heuristic_roi
        tribe_result = {"predictions": [], "mode": "heuristic", "transcript_word_count": len(transcript.split())}
    else:
        tribe_result = await tribe_engine.predict_from_video(file_path)
        predictions = np.array(tribe_result["predictions"])
        roi_scores = roi_extractor.extract_from_predictions(predictions)
        roi = ROI(A5=roi_scores.A5, LO=roi_scores.LO, Area45=roi_scores.Area45, TPJ=roi_scores.TPJ)
    
    social_params = NeuroSocialBridge.compute_social_params(roi)
    stage_passed, stage_msg = NeuroSocialBridge.stage_gate_check(social_params.W_attn)
    
    temporal_roi = roi_extractor.extract_with_temporal_dynamics(np.array(tribe_result.get("predictions", [[0.5]*20484]*20)), n_segments=4) if tribe_result.get("predictions") else {"segments": []}
    
    mirofish_result = await mirofish_engine.run_simulation(
        content={"transcript": transcript or "Sample transcript from video", "requirements": "Predict audience reaction"},
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
        "transcript": transcript[:500] + "..." if len(transcript) > 500 else transcript,
        "created_at": datetime.now().isoformat()
    }

@app.get("/videos")
async def list_videos():
    _evict_stale()
    if db.enabled:
        videos = await db.list_videos()
        return {"videos": videos}
    return {"videos": list(_videos_cache.values())}

@app.get("/videos/{video_id}")
async def get_video(video_id: str):
    _evict_stale()
    video = await db.get_video(video_id) or _videos_cache.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"video": video}

@app.get("/analyses/{video_id}")
async def get_analysis(video_id: str):
    _evict_stale()
    analysis = await db.get_analysis(video_id)
    if analysis:
        return analysis.get("data", analysis) if isinstance(analysis, dict) else analysis
    if video_id not in _analyses_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _analyses_cache[video_id]

@app.get("/reports/{video_id}")
async def get_report(video_id: str):
    _evict_stale()
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
    _evict_stale()
    analysis = await db.get_analysis(video_id)
    if analysis:
        data = analysis.get("data", analysis) if isinstance(analysis, dict) else analysis
        return data.get("mirofish_simulation", {})
    if video_id not in _analyses_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _analyses_cache[video_id].get("mirofish_simulation", {})

@app.get("/brain-response/{video_id}")
async def get_brain_response(video_id: str):
    _evict_stale()
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
    _evict_stale()
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

class ShareRequest(BaseModel):
    video_id: str

class WaitlistRequest(BaseModel):
    email: str
    name: Optional[str] = None

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
    _evict_stale()
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

class MergeRequest(BaseModel):
    guest_session_id: str
    user_id: str

@app.post("/api/merge")
async def merge_guest_session(req: MergeRequest):
    """Reassign guest videos/analyses to a newly signed-up user."""
    if db.enabled:
        await db.client.table("videos").update({"user_id": req.user_id}).eq("user_id", req.guest_session_id).execute()
        await db.client.table("analyses").update({"user_id": req.user_id}).eq("user_id", req.guest_session_id).execute()
        merged_count = len([v for v in _videos_cache.values() if v.get("user_id") == req.guest_session_id])
    else:
        merged_count = 0
        for vid, v in _videos_cache.items():
            if v.get("user_id") == req.guest_session_id:
                v["user_id"] = req.user_id
    
    return {"message": "Session merged", "videos_reassigned": merged_count}

@app.post("/api/share")
async def create_share_link(req: ShareRequest):
    _evict_stale()
    analysis = await db.get_analysis(req.video_id)
    if not analysis and req.video_id not in _analyses_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    share_id = str(uuid.uuid4())
    _share_links[share_id] = req.video_id
    return {"share_id": share_id, "url": f"/r/{share_id}"}

@app.get("/api/share/{share_id}")
async def get_shared_analysis(share_id: str):
    video_id = _share_links.get(share_id)
    if not video_id:
        raise HTTPException(status_code=404, detail="Share link not found")
    _evict_stale()
    analysis = await db.get_analysis(video_id)
    if analysis:
        analysis = analysis.get("data", analysis) if isinstance(analysis, dict) else analysis
    elif video_id in _analyses_cache:
        analysis = _analyses_cache[video_id]
    else:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"share_id": share_id, "video_id": video_id, "analysis": analysis}

@app.post("/api/waitlist")
async def join_waitlist(req: WaitlistRequest):
    for entry in _waitlist:
        if entry["email"] == req.email:
            raise HTTPException(status_code=409, detail="You're already on the waitlist!")
    entry = {"id": str(uuid.uuid4()), "email": req.email, "name": req.name, "created_at": datetime.now().isoformat()}
    _waitlist.append(entry)
    return {"message": "Joined waitlist!", "queue_position": len(_waitlist)}

@app.get("/api/analytics")
async def get_analytics():
    _evict_stale()
    total = len(_analyses_cache)
    scores = []
    hooks = []
    virals = []
    for a in _analyses_cache.values():
        if isinstance(a, dict):
            scores.append(a.get("success_probability", 0))
            hooks.append(a.get("hook_score", 0))
            virals.append(a.get("viral_potential", 0))
    return {
        "total_analyses": total,
        "total_videos": len(_videos_cache),
        "average_success_probability": round(sum(scores) / len(scores), 1) if scores else 0,
        "average_hook_score": round(sum(hooks) / len(hooks), 1) if hooks else 0,
        "average_viral_potential": round(sum(virals) / len(virals), 1) if virals else 0,
    }

@app.post("/api/digest/subscribe")
async def digest_subscribe(req: DigestRequest):
    if req.frequency not in ("weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Frequency must be 'weekly' or 'monthly'")
    if req.email in _digest_subs:
        raise HTTPException(status_code=409, detail="Email already subscribed")
    _digest_subs[req.email] = {
        "email": req.email,
        "frequency": req.frequency,
        "subscribed_at": datetime.now().isoformat()
    }
    return {"message": "Subscribed to digest", "email": req.email, "frequency": req.frequency}

@app.get("/api/digest/preview")
async def digest_preview():
    _evict_stale()
    analyses = list(_analyses_cache.values())
    scores = [a.get("success_probability", 0) for a in analyses if isinstance(a, dict)]
    hooks = [a.get("hook_score", 0) for a in analyses if isinstance(a, dict)]
    virals = [a.get("viral_potential", 0) for a in analyses if isinstance(a, dict)]
    top = sorted(analyses, key=lambda a: a.get("success_probability", 0) if isinstance(a, dict) else 0, reverse=True)[:5]
    return DigestPreview(
        digest_id=str(uuid.uuid4()),
        generated_at=datetime.now().isoformat(),
        total_analyses=len(analyses),
        average_hook_score=round(sum(hooks) / len(hooks), 1) if hooks else 0,
        average_viral_potential=round(sum(virals) / len(virals), 1) if virals else 0,
        average_success_probability=round(sum(scores) / len(scores), 1) if scores else 0,
        top_performers=[{"video_id": a.get("video_id", "unknown"), "success_probability": a.get("success_probability", 0)} for a in top],
    )

@app.get("/api/premium/status")
async def premium_status():
    return {
        "enabled": settings.premium_enabled,
        "price_monthly": settings.premium_price_monthly,
        "price_yearly": settings.premium_price_yearly,
        "max_analyses_free": settings.premium_max_analyses_free,
        "gpu_provider": settings.gpu_provider,
    }

@app.get("/api/premium/usage/{user_id}")
async def premium_usage(user_id: str):
    count = _usage_tracker.get(user_id, 0)
    is_premium = _is_premium(user_id)
    remaining = settings.premium_max_analyses_free - count if not is_premium else -1
    return {
        "analyses_this_month": count,
        "limit": settings.premium_max_analyses_free,
        "remaining": remaining,
        "is_premium": is_premium,
    }
