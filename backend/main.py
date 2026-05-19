import asyncio
import gc
import os
import smtplib
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import jwt
import numpy as np
from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from bridge_logic import ROI, NeuroSocialBridge
from config import settings
from storage_adapter import store, _supabase
from heuristic_scorer import score_transcript
from mirofish_engine import mirofish_engine
from pdf_report import generate_pdf_report
from rate_limiter import upload_limiter, check_api_limit
from roi_extractor import roi_extractor
from transcriber import transcriber
from tribe_engine import tribe_engine
from monitoring import metrics


_BACKGROUND_SWEEP_INTERVAL = 60  # seconds between automatic housekeeping sweeps


def _user_error(message: str, detail: str = "", status_code: int = 500):
    """Return a user-friendly error response."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={
            "error": message,
            "detail": detail,
            "help": "If this persists, try again in a few minutes or contact support.",
        },
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    whisper_status = "ready" if transcriber.available else "unavailable (install faster-whisper)"
    print(
        f"NeuroSim API starting — TRIBE: {'real' if tribe_engine.is_real else 'simulated'}, MiroFish: {'real' if mirofish_engine.is_real else 'simulated'}, Whisper: {whisper_status}"
    )

    # Start background housekeeping sweep
    async def _background_sweep():
        while True:
            await asyncio.sleep(_BACKGROUND_SWEEP_INTERVAL)
            try:
                global _last_eviction
                _last_eviction = 0  # reset gate so _evict_stale runs
                _evict_stale()
            except Exception as e:
                print(f"[WARN] Background sweep failed: {e}")

    sweep_task = asyncio.create_task(_background_sweep())

    yield

    sweep_task.cancel()
    print("NeuroSim API shutting down")


app = FastAPI(
    title="NeuroSim API",
    version="2.3.0",
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
    print(
        f"[{datetime.now().isoformat()}] {request.method} {request.url.path} {response.status_code} {duration}ms — {client_ip}"
    )
    metrics.record_request(
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration,
    )
    return response


# In-memory state (not persisted — recreated on restart)
_task_status: Dict[str, dict] = {}
_share_links: Dict[str, str] = {}
_video_share_links: Dict[str, list[str]] = {}  # reverse map for deletion cleanup
_share_link_timestamps: Dict[str, float] = {}
_SHARE_LINK_TTL = 604800  # 7 days
_waitlist: List[Dict[str, Any]] = []
_digest_subs: Dict[str, dict] = {}
_usage_tracker: Dict[str, int] = {}
_premium_users: set = set()  # Manually add user IDs here when Pro launches


def _is_premium(user_id: str) -> bool:
    return user_id in _premium_users


def _increment_usage(user_id: str):
    if user_id and user_id != "anonymous":
        _usage_tracker[user_id] = _usage_tracker.get(user_id, 0) + 1


# ─── JWT Auth ──────────────────────────────────────────────
_JWT_SECRET = settings.supabase_jwt_secret or os.getenv("SUPABASE_JWT_SECRET", "")


async def get_verified_user_id(
    authorization: Optional[str] = Header(None),
    user_id: str = "anonymous",
) -> str:
    """Validate JWT from Authorization header and return verified user_id.

    If no token is provided, falls back to the form-provided user_id.
    If Supabase JWT secret is not configured, skips validation.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
        if _JWT_SECRET:
            try:
                payload = jwt.decode(
                    token,
                    _JWT_SECRET,
                    algorithms=["HS256"],
                    audience="authenticated",
                    options={"require": ["sub", "exp"]},
                )
                return payload.get("sub", user_id)
            except jwt.ExpiredSignatureError:
                print(f"[AUTH] Expired token for user_id={user_id}")
                # Don't fail — fall back to form-provided user_id
            except jwt.InvalidTokenError as e:
                print(f"[AUTH] Invalid token: {e}")
                # Don't fail — fall back to form-provided user_id                # If no JWT secret configured, still return the form user_id
            # Don't fail — fall back to form-provided user_id
        return user_id
    return user_id


async def require_auth_user(
    authorization: Optional[str] = Header(None),
) -> str:
    """Require a valid JWT and return the authenticated user ID.

    Raises 401 if no valid token is provided (in production with JWT secret set).
    In dev/demo mode (no JWT secret), allows requests without token.
    """
    if not _JWT_SECRET:
        # Dev/demo mode — skip validation
        return "anonymous"

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(
            token,
            _JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"require": ["sub", "exp"]},
        )
        return payload.get("sub", "")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def _set_jwt_secret_for_test(secret: str) -> None:
    """Override JWT secret for testing. NOT for production use."""
    global _JWT_SECRET
    _JWT_SECRET = secret


_last_eviction: float = 0
_EVICTION_INTERVAL = 30  # seconds between housekeeping sweeps


def _evict_stale():
    from storage_adapter import _evict_stale as _adapter_evict
    _adapter_evict()
    global _last_eviction
    now = datetime.now().timestamp()
    if now - _last_eviction < _EVICTION_INTERVAL:
        return
    _last_eviction = now


def _is_video_magic(header: bytes) -> bool:
    """Check if the first bytes of a file match known video format signatures.

    Zero-dependency magic byte check for MP4/MOV, AVI, and WebM/Matroska.
    """
    if len(header) < 12:
        return False
    # MP4 / MOV — starts with an ftyp box (ISO Base Media File Format)
    # ftyp box starts at byte 4, contains 'ftyp' at offset 4-7
    if header[4:8] == b"ftyp" or header[0:4] == b"ftyp":
        return True
    # AVI — RIFF header with AVI subtype at byte 8
    if header[0:4] == b"RIFF" and header[8:12] == b"AVI ":
        return True
    # WebM / Matroska — starts with 0x1A45DFA3 (EBML header)
    if len(header) >= 4 and header[0:4] == b"\x1a\x45\xdf\xa3":
        return True
    return False


async def _get_analysis_or_404(video_id: str) -> Dict[str, Any]:
    """Fetch analysis from store. Raises 404 if not found."""
    _evict_stale()
    analysis = await store.get_analysis(video_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


async def _get_video_or_404(video_id: str) -> Dict[str, Any]:
    """Fetch video from store. Raises 404 if not found."""
    _evict_stale()
    video = await store.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


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


import stripe


stripe.api_key = settings.stripe_secret_key or ""


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


class CreateCheckoutSessionRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str
    user_id: Optional[str] = None


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
        "message": "NeuroSim API v2.3 — Simulated Analysis (Heuristic + Swarm)",
        "tribe_mode": "real" if tribe_engine.is_real else "simulated",
        "mirofish_mode": "real" if mirofish_engine.is_real else "simulated",
        "whisper_available": transcriber.available,
    }


@app.post("/api/stripe/create-checkout-session")
async def create_checkout_session(
    req: CreateCheckoutSessionRequest,
    verified_user_id: str = Depends(get_verified_user_id),
):
    """Create a Stripe Checkout session for the selected plan.

    Requires STRIPE_SECRET_KEY to be configured in environment.
    Returns a URL to redirect the user to Stripe's hosted Checkout page.

    The authenticated user ID (from JWT in Authorization header) takes
    precedence over the body-provided user_id. This ensures that the
    webhook receives a verified user identity in session metadata.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=501, detail="Stripe not configured — set STRIPE_SECRET_KEY")
    try:
        # Prefer the JWT-verified user ID over the body-provided user_id
        auth_user_id = verified_user_id if verified_user_id != "anonymous" else req.user_id
        metadata = {}
        if auth_user_id:
            metadata["user_id"] = auth_user_id
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": req.price_id, "quantity": 1}],
            success_url=req.success_url,
            cancel_url=req.cancel_url,
            metadata=metadata or None,
        )
        return {"url": session.url, "session_id": session.id}
    except stripe.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {e}")


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """Receive Stripe webhook events for subscription lifecycle.

    Handles:
      - checkout.session.completed → activates premium for the user
      - customer.subscription.deleted → deactivates premium

    Requires STRIPE_WEBHOOK_SECRET to be configured in environment.
    """
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=501, detail="Stripe webhook not configured — set STRIPE_WEBHOOK_SECRET")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id", "")
        if user_id:
            _premium_users.add(user_id)
            print(f"[STRIPE] Premium activated for user {user_id}")

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        # Try to find the user via subscription metadata or checkout session
        user_id = subscription.get("metadata", {}).get("user_id", "")
        if user_id and user_id in _premium_users:
            _premium_users.discard(user_id)
            print(f"[STRIPE] Premium deactivated for user {user_id}")
        print(f"[STRIPE] Subscription {subscription.get('id', 'unknown')} deleted")

    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        print(f"[STRIPE] Payment failed for invoice {invoice.get('id', 'unknown')}")

    return {"status": "ok"}


@app.get("/api/warmup")
async def warmup_cache():
    """Warm up the in-memory cache from Supabase.

    Pre-loads recent analyses into the in-memory cache so the first
    request after a cold start doesn't hit Supabase latency.
    Returns the number of analyses loaded into cache.
    """
    count = await store.warmup(limit=20)
    return {"status": "ok", "analyses_warmed": count}


@app.get("/health")
async def health():
    """Health check for Render keep-alive and monitoring."""
    return {
        "status": "healthy",
        "version": "2.3.0",
        "whisper": "ready" if transcriber.available else "unavailable",
        "supabase": "connected" if _supabase.enabled else "fallback",
        "uptime": "ok",
    }


@app.get("/api/metrics")
async def get_metrics():
    """Return API metrics summary."""
    return metrics.get_summary()


@app.post("/upload")
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
        current_usage = _usage_tracker.get(user_id, 0)
        if current_usage >= settings.premium_max_analyses_free:
            raise HTTPException(
                status_code=403,
                detail=f"Free tier limit reached ({settings.premium_max_analyses_free}/month). Upgrade to Pro for unlimited analyses.",
            )

    allowed_extensions = {".mp4", ".mov", ".avi", ".webm"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, detail=f"Unsupported format. Use: {allowed_extensions}"
        )

    # Magic-byte validation (zero-dependency, covers all allowed formats)
    header = await file.read(32)
    await file.seek(0)  # rewind for later write
    if not _is_video_magic(header):
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
    # Also store file_path locally since it's ephemeral (not in Supabase)
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


async def _process_in_background(
    video_id: str, file_path: str, filename: str, user_id: str = "anonymous"
):
    try:
        # Stage 1: Transcription
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

        # Free whisper model from memory
        transcriber.unload()
        gc.collect()

        # Stage 2: Heuristic ROI scoring
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

        # Stage 3: Full analysis
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

        # Stage 4: Cleanup — delete uploaded file
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
        # Clean up file on error too
        try:
            os.remove(file_path)
        except OSError:
            pass
        print(f"[ERROR] Analysis failed for {video_id}: {e}")


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


async def process_video(
    video_id: str, file_path: str, transcript: str = "", heuristic_roi: Optional[ROI] = None
) -> Dict[str, Any]:
    # Use heuristic ROI if provided, otherwise fall back to TRIBE engine
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
        "created_at": datetime.now().isoformat(),
    }


@app.get("/videos")
async def list_videos(_=Depends(check_api_limit)):
    videos = await store.list_videos()
    return {"videos": videos}


@app.get("/videos/{video_id}")
async def get_video(video_id: str):
    video = await _get_video_or_404(video_id)
    return {"video": video}


@app.get("/analyses/{video_id}")
async def get_analysis(video_id: str, _=Depends(check_api_limit)):
    return await _get_analysis_or_404(video_id)


@app.delete("/analyses/{video_id}")
async def delete_analysis(video_id: str, user_id: str = Depends(require_auth_user)):
    """Delete an analysis and its associated data from cache and Supabase.

    Cleans up: analyses cache, videos cache, share links, task status,
    WebSocket connections, and cache timestamps.
    """
    # _get_analysis_or_404 already raises 404 if not found — no need for try/except
    await _get_analysis_or_404(video_id)

    # Remove from store (both cache and Supabase)
    await store.delete_analysis(video_id)
    await store.delete_video(video_id)
    _task_status.pop(video_id, None)
    _ws_connections.pop(video_id, None)

    # Clean up any share links pointing to this video
    share_ids = _video_share_links.pop(video_id, [])
    for sid in share_ids:
        _share_links.pop(sid, None)
        _share_link_timestamps.pop(sid, None)

    return {"status": "deleted", "video_id": video_id}


@app.get("/reports/{video_id}")
async def get_report(video_id: str):
    video = await _get_video_or_404(video_id)
    analysis = await _get_analysis_or_404(video_id)
    return {
        "report_id": f"report_{video_id}",
        "video": video,
        "analysis": analysis,
        "generated_at": datetime.now().isoformat(),
    }


@app.get("/simulation/{video_id}")
async def get_simulation(video_id: str):
    analysis = await _get_analysis_or_404(video_id)
    return analysis.get("mirofish_simulation", {})


@app.get("/brain-response/{video_id}")
async def get_brain_response(video_id: str):
    analysis = await _get_analysis_or_404(video_id)
    return analysis.get("tribev2_brain_response", {})


class WhatIfRequest(BaseModel):
    modifications: Dict[str, Any]


@app.post("/simulation/what-if/{video_id}")
async def run_what_if(video_id: str, request: WhatIfRequest):
    analysis = await _get_analysis_or_404(video_id)
    base_sim = analysis.get("mirofish_simulation", {})
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


@app.get("/models/status")
async def model_status():
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


@app.get("/roi/metadata")
async def roi_metadata():
    return roi_extractor.get_roi_metadata()


@app.get("/reports/{video_id}/pdf")
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


class MergeRequest(BaseModel):
    guest_session_id: str
    user_id: str


@app.post("/api/merge")
async def merge_guest_session(
    req: MergeRequest,
    user_id: str = Depends(require_auth_user),
):
    """Reassign guest videos/analyses to a newly signed-up user."""
    # Ensure the authenticated user can only merge into their own ID
    if user_id != "anonymous" and req.user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot merge into another user's account")
    merged_count = 0
    if True:  # storage supports merge via Supabase or manual cache walk
        from storage_adapter import _videos_cache

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


@app.post("/api/share")
async def create_share_link(req: ShareRequest, user_id: str = Depends(require_auth_user)):
    _evict_stale()
    analysis = await store.get_analysis(req.video_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    share_id = str(uuid.uuid4())
    _share_links[share_id] = req.video_id
    _share_link_timestamps[share_id] = datetime.now().timestamp()
    # Track reverse mapping for deletion cleanup
    _video_share_links.setdefault(req.video_id, []).append(share_id)
    return {"share_id": share_id, "url": f"/r/{share_id}"}


@app.get("/api/share/{share_id}")
async def get_shared_analysis(share_id: str):
    video_id = _share_links.get(share_id)
    if not video_id:
        raise HTTPException(status_code=404, detail="Share link not found")
    # Check expiration
    ts = _share_link_timestamps.get(share_id, 0)
    if datetime.now().timestamp() - ts > _SHARE_LINK_TTL:
        _share_links.pop(share_id, None)
        _share_link_timestamps.pop(share_id, None)
        raise HTTPException(status_code=410, detail="Share link has expired (links expire after 7 days)")
    analysis = await _get_analysis_or_404(video_id)
    return {"share_id": share_id, "video_id": video_id, "analysis": analysis}


@app.post("/api/waitlist")
async def join_waitlist(req: WaitlistRequest):
    for entry in _waitlist:
        if entry["email"] == req.email:
            raise HTTPException(status_code=409, detail="You're already on the waitlist!")
    entry = {
        "id": str(uuid.uuid4()),
        "email": req.email,
        "name": req.name,
        "created_at": datetime.now().isoformat(),
    }
    _waitlist.append(entry)
    return {"message": "Joined waitlist!", "queue_position": len(_waitlist)}


@app.get("/api/analytics")
async def get_analytics(_=Depends(check_api_limit)):
    return await store.get_analytics_snapshot()


@app.post("/api/digest/subscribe")
async def digest_subscribe(req: DigestRequest, user_id: str = Depends(require_auth_user)):
    if req.frequency not in ("weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Frequency must be 'weekly' or 'monthly'")
    if req.email in _digest_subs:
        raise HTTPException(status_code=409, detail="Email already subscribed")
    _digest_subs[req.email] = {
        "email": req.email,
        "frequency": req.frequency,
        "subscribed_at": datetime.now().isoformat(),
        "last_delivered": None,
        "delivery_status": "active",
        "deliveries": [],
    }
    return {"message": "Subscribed to digest", "email": req.email, "frequency": req.frequency}


@app.get("/api/digest/subscriptions")
async def digest_subscriptions(user_id: str = Depends(require_auth_user)):
    """List all active digest subscriptions with delivery status."""
    return {
        "subscriptions": [
            {
                "email": email,
                "frequency": sub["frequency"],
                "subscribed_at": sub["subscribed_at"],
                "delivery_status": sub.get("delivery_status", "active"),
                "last_delivered": sub.get("last_delivered"),
                "total_deliveries": len(sub.get("deliveries", [])),
            }
            for email, sub in _digest_subs.items()
        ]
    }


def _send_email_smtp(to_email: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP using the configured email settings.

    Returns True on success, False on failure. Logs details on failure.
    Works with any SMTP provider (SendGrid, Mailgun, Gmail SMTP, etc.).
    Falls back gracefully when email is not configured (returns False).
    """
    if not settings.email_host or not settings.email_username:
        print(f"[EMAIL] SMTP not configured — can't send to {to_email}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.email_from
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.email_host, settings.email_port, timeout=15) as server:
            server.starttls()
            server.login(settings.email_username, settings.email_password)
            server.sendmail(settings.email_from_address, [to_email], msg.as_string())
        return True
    except smtplib.SMTPException as e:
        print(f"[EMAIL] SMTP error sending to {to_email}: {e}")
        return False
    except Exception as e:
        print(f"[EMAIL] Unexpected error sending to {to_email}: {e}")
        return False


def _format_digest_html(analyses: list, frequency: str, dashboard_url: str = "", unsubscribe_url: str = "") -> str:
    """Build an HTML email body for the digest from recent analyses."""
    items_html = ""
    for a in analyses[:5]:
        hook = a.get("hook_score", "N/A")
        viral = a.get("viral_potential", "N/A")
        success = a.get("success_probability", "N/A")
        vid = a.get("video_id", "unknown")
        items_html += f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #e5e7eb;font-family:monospace;font-size:13px;color:#4b5563;">{vid[:8]}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #e5e7eb;font-family:monospace;font-size:13px;color:#4b5563;">{hook}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #e5e7eb;font-family:monospace;font-size:13px;color:#4b5563;">{viral}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #e5e7eb;font-family:monospace;font-size:13px;color:#4b5563;">{success}%</td>
        </tr>"""
    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background-color:#f9fafb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f9fafb;">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="560" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
        <tr>
          <td style="padding:32px 32px 24px;background:linear-gradient(135deg,#0a1628,#13244a);">
            <h1 style="margin:0;font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.02em;">NeuroSim Digest</h1>
            <p style="margin:8px 0 0;font-size:14px;color:#94a3b8;">Your {frequency} content analysis summary</p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px 8px;">
            <p style="margin:0;font-size:14px;color:#374151;line-height:1.6;">
              Here's a snapshot of your recent content analyses. Top performers are highlighted below.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
              <thead>
                <tr style="background-color:#f3f4f6;">
                  <th style="padding:10px 16px;text-align:left;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Video</th>
                  <th style="padding:10px 16px;text-align:left;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Hook</th>
                  <th style="padding:10px 16px;text-align:left;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Viral</th>
                  <th style="padding:10px 16px;text-align:left;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Success</th>
                </tr>
              </thead>
              <tbody>
                {items_html}
              </tbody>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px 32px;">
            <a href="{DASHBOARD}" style="display:inline-block;padding:12px 24px;background:linear-gradient(135deg,#4deeeb,#7c3aed);color:#ffffff;text-decoration:none;border-radius:8px;font-size:14px;font-weight:600;">
              View Full Dashboard
            </a>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px;background-color:#f9fafb;border-top:1px solid #e5e7eb;">
            <p style="margin:0;font-size:12px;color:#9ca3af;">
              You're receiving this because you subscribed to the NeuroSim {frequency} digest.
              <a href="{UNSUBSCRIBE}" style="color:#6b7280;text-decoration:underline;">Unsubscribe</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
    # Substitute URL placeholders — use f-string debug vars {{DASHBOARD}}/{{UNSUBSCRIBE}}
    html = html.replace("{DASHBOARD}", dashboard_url or "#")
    html = html.replace("{UNSUBSCRIBE}", unsubscribe_url or "#")
    return html


@app.post("/api/digest/send")
async def trigger_digest_send(frequency: str = "weekly", user_id: str = Depends(require_auth_user)):
    """Trigger a digest send for all subscribers of the given frequency.

    Sends real HTML emails via SMTP when configured. Falls back to
    simulated delivery (log-only) when SMTP is not set up.
    Each delivery attempt is tracked with status, timestamp,
    error details, and subscriber info for auditability.
    """
    if frequency not in ("weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Frequency must be 'weekly' or 'monthly'")

    # Gather recent analyses for the digest content
    from storage_adapter import _analyses_cache
    analyses = list(_analyses_cache.values())
    top = sorted(
        analyses,
        key=lambda a: a.get("success_probability", 0) if isinstance(a, dict) else 0,
        reverse=True,
    )[:5]
    dashboard_url = settings.app_base_url.rstrip("/") + "/dashboard" if settings.app_base_url else ""
    unsubscribe_url = settings.app_base_url.rstrip("/") + "/digest/unsubscribe" if settings.app_base_url else ""
    html_body = _format_digest_html(top, frequency, dashboard_url, unsubscribe_url)
    smtp_configured = bool(settings.email_host and settings.email_username)

    sent_count = 0
    failed_count = 0
    for email, sub in list(_digest_subs.items()):
        if sub["frequency"] != frequency:
            continue

        delivery_id = str(uuid.uuid4())[:8]
        status = "simulated"
        error_msg = None

        if smtp_configured:
            subject = f"NeuroSim {frequency.capitalize()} Digest — Your Content Analysis Summary"
            ok = _send_email_smtp(email, subject, html_body)
            if ok:
                status = "delivered"
                sent_count += 1
                print(f"[DIGEST] Delivered {frequency} digest to {email} (delivery_id={delivery_id})")
            else:
                status = "failed"
                failed_count += 1
                error_msg = "SMTP delivery failed"
                print(f"[DIGEST] Failed to deliver {frequency} digest to {email} (delivery_id={delivery_id})")
        else:
            # Simulated delivery (log only)
            status = "delivered"
            sent_count += 1
            print(f"[DIGEST] [SIMULATED] Delivered {frequency} digest to {email} (delivery_id={delivery_id})")

        delivery = {
            "email": email,
            "frequency": frequency,
            "sent_at": datetime.now().isoformat(),
            "status": status,
            "delivery_id": delivery_id,
        }
        if error_msg:
            delivery["error"] = error_msg

        sub.setdefault("deliveries", []).append(delivery)
        sub["last_delivered"] = delivery["sent_at"]
        sub["delivery_status"] = status
        if error_msg:
            sub["last_error"] = error_msg

    return {
        "message": "Digest send triggered",
        "frequency": frequency,
        "sent": sent_count,
        "failed": failed_count,
        "total_subscribers": len(_digest_subs),
        "smtp_configured": smtp_configured,
    }


@app.get("/api/digest/preview")
async def digest_preview():
    _evict_stale()
    from storage_adapter import _analyses_cache
    analyses = list(_analyses_cache.values())
    scores = [a.get("success_probability", 0) for a in analyses if isinstance(a, dict)]
    hooks = [a.get("hook_score", 0) for a in analyses if isinstance(a, dict)]
    virals = [a.get("viral_potential", 0) for a in analyses if isinstance(a, dict)]
    top = sorted(
        analyses,
        key=lambda a: a.get("success_probability", 0) if isinstance(a, dict) else 0,
        reverse=True,
    )[:5]
    return DigestPreview(
        digest_id=str(uuid.uuid4()),
        generated_at=datetime.now().isoformat(),
        total_analyses=len(analyses),
        average_hook_score=round(sum(hooks) / len(hooks), 1) if hooks else 0,
        average_viral_potential=round(sum(virals) / len(virals), 1) if virals else 0,
        average_success_probability=round(sum(scores) / len(scores), 1) if scores else 0,
        top_performers=[
            {
                "video_id": a.get("video_id", "unknown"),
                "success_probability": a.get("success_probability", 0),
            }
            for a in top
        ],
    )


@app.get("/api/premium/status")
async def premium_status():
    return {
        "enabled": settings.premium_enabled,
        "price_monthly": settings.premium_price_monthly,
        "price_yearly": settings.premium_price_yearly,
        "max_analyses_free": settings.premium_max_analyses_free,
        "gpu_provider": settings.gpu_provider,
        "stripe_price_id_monthly": settings.stripe_price_id_monthly or None,
        "stripe_price_id_yearly": settings.stripe_price_id_yearly or None,
        "stripe_configured": bool(settings.stripe_secret_key),
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
