import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

import sentry_sdk
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bridge_logic import ROI, NeuroSocialBridge
from config import settings
from storage_adapter import store, _supabase
from heuristic_scorer import score_transcript
from mirofish_engine import mirofish_engine
from rate_limiter import upload_limiter, check_api_limit
from roi_extractor import roi_extractor
from transcriber import transcriber
from tribe_engine import tribe_engine
from monitoring import metrics

# ─── Shared state (re-exported for test compatibility) ────
from shared_state import (
    _task_status,
    _share_links,
    _video_share_links,
    _share_link_timestamps,
    _SHARE_LINK_TTL,
    _waitlist,
    _digest_subs,
    _usage_tracker,
    _premium_users,
    _ws_connections,
    _last_eviction,
    _evict_stale,
    _is_premium,
    _increment_usage,
    _get_analysis_or_404,
    _get_video_or_404,
    get_verified_user_id,
    require_auth_user,
    _set_jwt_secret_for_test,
)
from routes.digest import _send_email_smtp
from routes.predict import router as predict_router
from vision_scorer import vision_scorer

# ─── Route modules ─────────────────────────────────────────
from routes.auth import router as auth_router
from routes.upload import router as upload_router
from routes.analysis import router as analysis_router
from routes.share import router as share_router
from routes.premium import router as premium_router
from routes.digest import router as digest_router
from routes.ab_testing import router as ab_testing_router
from routes.waitlist import router as waitlist_router


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
    # Initialize Sentry
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.sentry_environment,
            traces_sample_rate=0.1,
        )
        logger.info(f"Sentry initialized — environment: {settings.sentry_environment}")

    # Initialize PostHog
    if settings.posthog_api_key:
        import posthog
        posthog.api_key = settings.posthog_api_key
        posthog.host = settings.posthog_host
        logger.info("PostHog initialized")

    os.makedirs(settings.upload_dir, exist_ok=True)
    whisper_status = "ready" if transcriber.available else "unavailable (install faster-whisper)"
    vision_status = "enabled" if vision_scorer.enabled else "disabled (no GEMINI_API_KEY)"
    logger.info(
        f"NeuroSim API starting — TRIBE: {'real' if tribe_engine.is_real else 'simulated'}, "
        f"MiroFish: {'real' if mirofish_engine.is_real else 'simulated'}, "
        f"Whisper: {whisper_status}, Vision: {vision_status}"
    )

    async def _background_sweep():
        import shared_state
        while True:
            await asyncio.sleep(_BACKGROUND_SWEEP_INTERVAL)
            try:
                shared_state._last_eviction = 0
                _evict_stale()
            except Exception as e:
                logger.warning(f"Background sweep failed: {e}")

    sweep_task = asyncio.create_task(_background_sweep())

    yield

    sweep_task.cancel()
    logger.info("NeuroSim API shutting down")


app = FastAPI(
    title="NeuroSim API",
    version="3.0.0",
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
    logger.info(
        f"[{datetime.now().isoformat()}] {request.method} {request.url.path} {response.status_code} {duration}ms — {client_ip}"
    )
    metrics.record_request(
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration,
    )
    return response


# ─── Include route modules ─────────────────────────────────
# All routes are versioned under /api/v1/
API_PREFIX = f"/api/{settings.api_version}"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(upload_router, prefix=API_PREFIX)
app.include_router(analysis_router, prefix=API_PREFIX)
app.include_router(share_router, prefix=API_PREFIX)
app.include_router(premium_router, prefix=API_PREFIX)
app.include_router(digest_router, prefix=API_PREFIX)
app.include_router(predict_router, prefix=API_PREFIX)
app.include_router(ab_testing_router)
app.include_router(waitlist_router)


# ─── Pydantic models for remaining routes ──────────────────

# ─── Remaining inline routes ───────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "NeuroSim API v3.0 — Heuristic + Vision Analysis (Simulated Analysis)",
        "tribe_mode": "real" if tribe_engine.is_real else "simulated",
        "mirofish_mode": "real" if mirofish_engine.is_real else "simulated",
        "whisper_available": transcriber.available,
        "vision_enabled": vision_scorer.enabled,
    }


@app.get("/warmup")
async def warmup_cache():
    """Warm up the in-memory cache from Supabase."""
    count = await store.warmup(limit=20)
    return {"status": "ok", "analyses_warmed": count}


@app.get("/health")
async def health():
    """Health check for Render keep-alive and monitoring."""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "whisper": "ready" if transcriber.available else "unavailable",
        "supabase": "connected" if _supabase.enabled else "fallback",
        "uptime": "ok",
    }


@app.get("/metrics")
async def get_metrics():
    """Return API metrics summary."""
    return metrics.get_summary()


@app.get("/analytics")
async def get_analytics(_=Depends(check_api_limit)):
    return await store.get_analytics_snapshot()


class ErrorReportRequest(BaseModel):
    message: str
    stack: Optional[str] = None
    url: str
    timestamp: str
    userAgent: str


@app.post("/error-report")
async def report_error(req: ErrorReportRequest, _=Depends(check_api_limit)):
    """Receive frontend error reports for monitoring."""
    logger.info(f"[FRONTEND-ERROR] {req.message} at {req.url}")
    if req.stack:
        logger.info(f"[FRONTEND-ERROR] Stack: {req.stack[:500]}")
    return {"status": "received"}
