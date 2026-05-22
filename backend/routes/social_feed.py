"""Social Feed Simulator route module.

Simulates scroll retention, choosing-to-watch thresholds (VTR), scroll velocity,
and platform-specific recommendation weights (TikTok, YouTube Shorts, Reels)
based on neuro-feedback ROI scores and transcript patterns.
"""

import logging
import uuid
import math
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from storage_adapter import store
from shared_state import get_verified_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["social-feed"])


class SocialFeedSimulationRequest(BaseModel):
    video_id: str = Field(..., description="The ID of the analyzed video/script baseline.")
    platform: str = Field(..., description="The platform to simulate: 'tiktok', 'shorts', or 'reels'.")
    sound_trend_factor: float = Field(0.5, ge=0.0, le=1.0, description="The sound trend multiplier (0.0 to 1.0) representing trending audio virality.")


@router.post("/simulation/social-feed")
async def create_social_feed_simulation(
    req: SocialFeedSimulationRequest,
    user_id: str = Depends(get_verified_user_id),
):
    """Generate a second-by-second social feed simulation for a platform."""
    platform = req.platform.lower()
    if platform not in ("tiktok", "shorts", "reels"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported platform. Choose from: 'tiktok', 'shorts', 'reels'"
        )

    # 1. Fetch analysis
    analysis = await store.get_analysis(req.video_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    hook_score = float(analysis.get("hook_score", 50.0))
    success_probability = float(analysis.get("success_probability", 50.0))

    # Helper to extract brain region scores (0 to 100) robustly
    def get_region(region_name: str, default: float = 50.0) -> float:
        # Check inside analysis_response.cortical_response
        response = analysis.get("analysis_response", {})
        if isinstance(response, dict):
            cortical = response.get("cortical_response", {})
            if isinstance(cortical, dict) and region_name in cortical:
                return float(cortical[region_name])
            # Fallback to direct brain_regions or direct key
            brain_regs = response.get("brain_regions", {})
            if isinstance(brain_regs, dict) and region_name in brain_regs:
                val = brain_regs[region_name]
                return float(val * 100.0 if val <= 1.0 else val)
        # Check root brain_regions
        brain_regs = analysis.get("brain_regions", {})
        if isinstance(brain_regs, dict) and region_name in brain_regs:
            val = brain_regs[region_name]
            return float(val * 100.0 if val <= 1.0 else val)
        return default

    # 2. Extract or Synthesize baseline engagement curve
    raw_curve = analysis.get("engagement_curve")
    if not raw_curve:
        # Synthesize baseline curve of 15 seconds
        hook_val = hook_score / 100.0
        raw_curve = []
        current_att = hook_val
        for i in range(15):
            decay_rate = 0.05 + 0.05 * (1.0 - hook_val)
            current_att = max(0.05, current_att * (1.0 - decay_rate))
            raw_curve.append(current_att)
    else:
        raw_curve = [float(x) for x in raw_curve]

    # 3. Platform-specific retention and scroll modeling
    platform_curve = []
    velocity_curve = []
    alerts = []
    loop_count = 1.0

    if platform == "tiktok":
        # Average loop count is driven by auditory triggers (A5) and watch percentage
        auditory_val = get_region("auditory_cortex") / 100.0
        avg_watch_est = sum(raw_curve) / len(raw_curve) if raw_curve else 0.5
        loop_count = round(1.0 + 1.8 * auditory_val * avg_watch_est, 2)
        loop_count = min(3.5, max(1.0, loop_count))

        # View-Through Rate: early hook attention & auditory cues
        vtr = 0.25 + 0.5 * (hook_score / 100.0) + 0.2 * auditory_val
        vtr = min(0.95, max(0.05, vtr))

        # Check early hook attention (first 2 seconds)
        first_2s_avg = sum(raw_curve[:2]) / min(2, len(raw_curve)) if raw_curve else 0.5
        drop_active = first_2s_avg < 0.40

        for i, val in enumerate(raw_curve):
            if drop_active and i >= 2:
                # Exponential drop due to hooks fading early
                decay_mult = math.exp(-0.16 * (i - 1))
                platform_curve.append(max(0.02, val * decay_mult))
            else:
                # Normal TikTok boost for strong auditory/hook trigger
                boost = 0.06 * auditory_val
                platform_curve.append(min(1.0, val + boost))

    elif platform == "shorts":
        visual_val = get_region("visual_cortex") / 100.0
        # Choose-to-watch threshold (VTR): prefrontal visual hook focus
        vtr = 0.2 + 0.5 * (hook_score / 100.0) + 0.3 * visual_val
        vtr = min(0.95, max(0.05, vtr))

        # Visual boosts for the first 5 seconds
        vis_boost = 0.08 * visual_val
        for i, val in enumerate(raw_curve):
            if i < 5:
                platform_curve.append(min(1.0, val + vis_boost))
            else:
                # Normal decay modified by VTR factor
                vtr_decay = 0.06 * (1.0 - vtr)
                platform_curve.append(max(0.02, val * (1.0 - vtr_decay)))

    else:  # Reels
        emotional_val = get_region("amygdala") / 100.0
        # Sound trend acted as a huge factor
        vtr = 0.3 + 0.4 * (hook_score / 100.0) + 0.3 * req.sound_trend_factor
        vtr = min(0.95, max(0.05, vtr))

        # Sound trend scales general exposure, and high emotional intensity boosts peak mid-video
        trend_boost = 0.12 * req.sound_trend_factor
        climax_idx = len(raw_curve) // 2
        for i, val in enumerate(raw_curve):
            curve_val = val * (1.0 + trend_boost)
            if i == climax_idx:
                curve_val += 0.15 * (emotional_val / 100.0)
            platform_curve.append(min(1.0, max(0.02, curve_val)))

    # 4. Generate second-by-second drop-off alerts
    for i in range(1, len(platform_curve)):
        drop = platform_curve[i - 1] - platform_curve[i]
        if drop > 0.07:  # >7% drop in 1 second is critical
            pct_lost = round(drop * 100)
            pct_remaining = round(platform_curve[i] * 100)
            if i < 3:
                alerts.append({
                    "second": i,
                    "severity": "critical" if drop > 0.12 else "high",
                    "message": f"Hook faded: {pct_lost}% of viewers swiped away ({pct_remaining}% remaining)."
                })
            elif i == len(platform_curve) // 2:
                alerts.append({
                    "second": i,
                    "severity": "medium",
                    "message": f"Mid-video lull: {pct_lost}% lost interest due to low visual/auditory stimuli."
                })
            else:
                alerts.append({
                    "second": i,
                    "severity": "low",
                    "message": f"Friction point: attention dipped by {pct_lost}%."
                })

    # 5. Compute swipe velocities (scrolls per minute)
    for val in platform_curve:
        # Base velocity logic: 40 * (1 - val) + 12 scrolls/min
        scroll_speed = round(42.0 * (1.0 - val) + 12.0, 1)
        velocity_curve.append(min(85.0, max(6.0, scroll_speed)))

    # 6. Algorithmic scoring
    avg_watch_pct = (sum(platform_curve) / len(platform_curve)) * 100.0

    if platform == "tiktok":
        # TikTok Score = 0.5 * Avg Watch % + 0.3 * (normalized Loop Count) + 0.2 * Auditory Attention
        normalized_loop = ((loop_count - 1.0) / 2.5) * 100.0 if loop_count > 1.0 else 0.0
        score = 0.5 * avg_watch_pct + 0.3 * normalized_loop + 0.2 * get_region("auditory_cortex")
    elif platform == "shorts":
        # Shorts Score = 0.6 * VTR + 0.3 * Average Viewer Duration + 0.1 * Visual Attention
        score = 0.6 * (vtr * 100.0) + 0.3 * avg_watch_pct + 0.1 * get_region("visual_cortex")
    else:  # Reels
        # Reels Score = 0.4 * Emotional Arc Peak + 0.4 * Sound Trend + 0.2 * Engagement (CTA)
        cta_score = float(analysis.get("cta_analysis", {}).get("cta_activation_score", 50.0))
        score = 0.4 * get_region("amygdala") + 0.4 * (req.sound_trend_factor * 100.0) + 0.2 * cta_score

    score = round(min(100.0, max(0.0, score)), 1)
    reach_multiplier = round(1.0 + 4.5 * (score / 100.0) * vtr, 2)

    retention_data = {
        "retention_curve": [round(x, 3) for x in platform_curve],
        "velocity_curve": velocity_curve,
        "alerts": alerts,
        "reach_multiplier": reach_multiplier,
        "loop_count": loop_count,
    }

    # 7. Persist to database & cache
    sim_id = f"sim_{uuid.uuid4().hex[:12]}"
    sim_record = await store.insert_social_simulation(
        sim_id=sim_id,
        video_id=req.video_id,
        platform=platform,
        algorithmic_score=score,
        vtr=vtr,
        retention_data=retention_data,
        user_id=user_id,
    )

    return sim_record


@router.get("/simulation/social-feed/{sim_id}")
async def get_social_feed_simulation(sim_id: str):
    """Retrieve details of a past social feed simulation."""
    sim = await store.get_social_simulation(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return sim


@router.get("/simulation/social-feed/history/{video_id}")
async def list_social_feed_simulations_for_video(
    video_id: str,
    user_id: str = Depends(get_verified_user_id),
):
    """List simulation histories for a specific video baseline under the user session."""
    sims = await store.list_social_simulations(user_id=user_id)
    # Filter by video_id
    video_sims = [sim for sim in sims if sim.get("video_id") == video_id]
    return video_sims


@router.delete("/simulation/social-feed/{sim_id}")
async def delete_social_feed_simulation(
    sim_id: str,
    user_id: str = Depends(get_verified_user_id),
):
    """Delete a past social feed simulation record."""
    sim = await store.get_social_simulation(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if sim.get("user_id") != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this simulation")

    await store.delete_social_simulation(sim_id)
    return {"status": "ok", "message": "Simulation deleted successfully."}
