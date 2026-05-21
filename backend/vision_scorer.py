"""Video vision analysis using Gemini 2.5 Flash.

Analyzes uploaded video clips for engagement patterns, hook strength,
hold rate, and per-second engagement curves. Maps to brain region
activation proxies for the 3D brain visualization.

Uses Google AI Studio free tier (gemini-2.5-flash). Falls back gracefully
when API key is not configured or rate-limited.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from config import settings

logger = logging.getLogger(__name__)

GEMINI_PROMPT = """Analyze this video clip and return ONLY valid JSON with these exact fields:
{
  "hook_score": 0.72,
  "hold_rate": 0.65,
  "virality_score": 68,
  "engagement_curve": [0.85, 0.72, 0.60, 0.45, 0.55, 0.40, 0.38, 0.42],
  "visual_engagement": 0.70,
  "audio_engagement": 0.65,
  "emotional_arc": 0.58,
  "cta_presence": 0.30,
  "peak_hook_timestamp": 1.0,
  "brain_regions": {
    "visual_cortex": 0.85,
    "auditory_cortex": 0.65,
    "amygdala": 0.58,
    "prefrontal": 0.40,
    "memory": 0.55,
    "social_cognition": 0.50
  },
  "recommendations": [
    "Start with motion or a human face in the first frame",
    "Add a curiosity gap or question within the first 3 seconds",
    "Increase visual contrast to maintain attention through the middle"
  ]
}

Scoring guidelines:
- hook_score (0-1): How well the first 3 seconds stop the scroll. Based on motion, contrast, human presence, salient objects.
- hold_rate (0-1): Predicted percentage of viewers who watch to the end. Based on pacing, content delivery, promise fulfillment.
- virality_score (0-100): Overall viral potential combining hook, hold, and emotional resonance.
- engagement_curve: Array of 0-1 values, one per second of video duration. Show how attention changes second by second.
- visual_engagement (0-1): Visual motion, contrast, composition quality, color dynamics.
- audio_engagement (0-1): Speech clarity, music presence, sound design, rhythm.
- emotional_arc (0-1): Emotional intensity, progression, and resonance throughout the clip.
- cta_presence (0-1): Presence and strength of call-to-action (verbal or visual).
- peak_hook_timestamp: The second number (0-based) where engagement is highest.
- brain_regions: Activation levels (0-1) for 6 brain regions. visual_cortex for visual attention, auditory_cortex for audio processing, amygdala for emotional response, prefrontal for rational processing, memory for memorability, social_cognition for empathy/connection.
- recommendations: 3-5 specific, actionable suggestions to improve the clip.

Score based on proven attention patterns: motion in first frame, human face presence, contrast changes, speech pacing, emotional peaks, curiosity gaps, pattern interrupts.
"""


class VisionScorer:
    """Analyze video clips using Gemini 2.5 Flash for engagement scoring."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")

        if model is not None:
            self.model = model
        else:
            self.model = settings.gemini_model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

        self.enabled = bool(self.api_key) and settings.vision_enabled
        self._client = None

    def _get_client(self):
        if self._client is None and self.enabled:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from Gemini response, handling markdown wrappers."""
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
            text = text.strip()
        return json.loads(text)

    def _validate_response(self, data: Dict) -> bool:
        """Validate that the response has all required fields with correct types."""
        required = {
            "hook_score": (int, float),
            "hold_rate": (int, float),
            "virality_score": (int, float),
            "engagement_curve": list,
            "visual_engagement": (int, float),
            "audio_engagement": (int, float),
            "emotional_arc": (int, float),
            "cta_presence": (int, float),
            "peak_hook_timestamp": (int, float),
            "brain_regions": dict,
            "recommendations": list,
        }
        for field, type_check in required.items():
            if field not in data:
                logger.warning(f"Missing field in Gemini response: {field}")
                return False
            if not isinstance(data[field], type_check):
                logger.warning(f"Wrong type for {field}: expected {type_check}, got {type(data[field])}")
                return False
        return True

    def _clamp(self, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        return max(min_val, min(max_val, float(value)))

    def analyze_video(self, file_path: str, max_retries: int = 2) -> Dict[str, Any]:
        """Analyze a video file and return engagement scores.

        Args:
            file_path: Path to the video file.
            max_retries: Number of retries on failure.

        Returns:
            Dict with hook_score, hold_rate, virality_score, engagement_curve,
            brain_regions, recommendations, and mode.
        """
        if not self.enabled:
            logger.info("Vision scoring disabled — no GEMINI_API_KEY configured")
            return {"mode": "disabled", "error": "Vision scoring not configured"}

        client = self._get_client()
        if client is None:
            return {"mode": "error", "error": "Failed to initialize Gemini client"}

        for attempt in range(max_retries + 1):
            uploaded_file = None
            try:
                import time
                from google.genai import types

                logger.info(f"Uploading video {file_path} to Gemini Files API...")
                uploaded_file = client.files.upload(file=file_path)

                def _get_state(f):
                    if hasattr(f, "state") and f.state:
                        if hasattr(f.state, "name"):
                            return str(f.state.name).upper()
                        return str(f.state).upper()
                    return ""

                state_str = _get_state(uploaded_file)

                while "PROCESSING" in state_str:
                    logger.info("Gemini is processing the video, waiting 1s...")
                    time.sleep(1)
                    uploaded_file = client.files.get(name=uploaded_file.name)
                    state_str = _get_state(uploaded_file)

                if "FAILED" in state_str:
                    raise ValueError(f"Gemini video processing failed: {state_str}")

                logger.info("Video is active in Gemini Files API. Running model generation...")
                response = client.models.generate_content(
                    model=self.model,
                    contents=[GEMINI_PROMPT, uploaded_file],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                )

                if not response.text:
                    raise ValueError("Empty response from Gemini")

                data = self._extract_json(response.text)

                if not self._validate_response(data):
                    raise ValueError(f"Invalid response structure: {data}")

                brain_regions = {}
                for region, value in data["brain_regions"].items():
                    brain_regions[region] = self._clamp(value)

                engagement_curve = [self._clamp(v) for v in data["engagement_curve"]]

                result = {
                    "hook_score": self._clamp(data["hook_score"]),
                    "hold_rate": self._clamp(data["hold_rate"]),
                    "virality_score": max(0, min(100, float(data["virality_score"]))),
                    "engagement_curve": engagement_curve,
                    "visual_engagement": self._clamp(data["visual_engagement"]),
                    "audio_engagement": self._clamp(data["audio_engagement"]),
                    "emotional_arc": self._clamp(data["emotional_arc"]),
                    "cta_presence": self._clamp(data["cta_presence"]),
                    "peak_hook_timestamp": float(data["peak_hook_timestamp"]),
                    "brain_regions": brain_regions,
                    "recommendations": data["recommendations"],
                    "mode": "vision",
                }

                logger.info(
                    f"Vision analysis complete: virality={result['virality_score']}, "
                    f"hook={result['hook_score']:.2f}, hold={result['hold_rate']:.2f}"
                )
                return result

            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Vision analysis failed after {max_retries} retries: {e}")
                    return {"mode": "error", "error": str(e)}
                logger.warning(f"Vision analysis attempt {attempt + 1} failed: {e}")
            finally:
                if uploaded_file is not None:
                    try:
                        client.files.delete(name=uploaded_file.name)
                        logger.info(f"Successfully deleted video {uploaded_file.name} from Gemini storage.")
                    except Exception as delete_err:
                        logger.warning(f"Failed to delete video {uploaded_file.name} from Gemini storage: {delete_err}")

        return {"mode": "error", "error": "Unexpected failure in vision analysis"}

    def get_fallback_scores(self, duration_seconds: int = 8) -> Dict[str, Any]:
        """Generate reasonable fallback scores when Gemini is unavailable."""
        return {
            "hook_score": 0.5,
            "hold_rate": 0.5,
            "virality_score": 50,
            "engagement_curve": [0.5] * max(1, duration_seconds),
            "visual_engagement": 0.5,
            "audio_engagement": 0.5,
            "emotional_arc": 0.5,
            "cta_presence": 0.5,
            "peak_hook_timestamp": 1.0,
            "brain_regions": {
                "visual_cortex": 0.5,
                "auditory_cortex": 0.5,
                "amygdala": 0.5,
                "prefrontal": 0.5,
                "memory": 0.5,
                "social_cognition": 0.5,
            },
            "recommendations": [],
            "mode": "fallback",
        }


vision_scorer = VisionScorer()
