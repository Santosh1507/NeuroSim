"""Merge heuristic ROI scores with vision analysis scores.

Vision scores dominate (they're from actual video understanding) but
heuristic scores act as a sanity check and fallback when Gemini is
rate-limited or unavailable.
"""

from typing import Any, Dict

from bridge_logic import ROI


def merge_signals(
    heuristic_roi: Dict[str, Any],
    vision_scores: Dict[str, Any],
) -> ROI:
    """Merge heuristic and vision scores into unified ROI.

    Args:
        heuristic_roi: From heuristic_scorer — keys A5, LO, Area45, TPJ (0-1)
        vision_scores: From vision_scorer — keys visual_engagement, audio_engagement,
                       emotional_arc, cta_presence (0-1)

    Returns:
        Unified ROI dataclass.
    """
    vision_mode = vision_scores.get("mode", "")

    if vision_mode in ("disabled", "error", "fallback"):
        return ROI(
            A5=heuristic_roi.get("A5", 0.5),
            LO=heuristic_roi.get("LO", 0.5),
            Area45=heuristic_roi.get("Area45", 0.5),
            TPJ=heuristic_roi.get("TPJ", 0.5),
        )

    v = vision_scores
    h = heuristic_roi

    merged_a5 = 0.55 * v.get("audio_engagement", 0.5) + 0.45 * h.get("A5", 0.5)
    merged_lo = 0.65 * v.get("visual_engagement", 0.5) + 0.35 * h.get("LO", 0.5)
    merged_45 = 0.60 * v.get("cta_presence", 0.5) + 0.40 * h.get("Area45", 0.5)
    merged_tpj = 0.55 * v.get("emotional_arc", 0.5) + 0.45 * h.get("TPJ", 0.5)

    return ROI(
        A5=round(min(1.0, max(0.0, merged_a5)), 3),
        LO=round(min(1.0, max(0.0, merged_lo)), 3),
        Area45=round(min(1.0, max(0.0, merged_45)), 3),
        TPJ=round(min(1.0, max(0.0, merged_tpj)), 3),
    )


def get_analysis_mode(heuristic_available: bool, vision_mode: str) -> str:
    """Determine the analysis mode string for the UI."""
    if vision_mode == "vision" and heuristic_available:
        return "vision+heuristic"
    if vision_mode == "vision":
        return "vision"
    if heuristic_available:
        return "heuristic"
    return "unknown"
