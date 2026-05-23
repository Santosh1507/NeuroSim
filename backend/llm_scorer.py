"""LLM-enhanced ROI scoring using Gemini 2.5 Flash.

Maps transcript text to 4 ROI dimensions via LLM:
  A5     — auditory cortex (pacing, rhythm, clarity)
  LO     — lateral occipital (visual/descriptive language)
  Area45 — Broca's area (CTA activation, persuasion)
  TPJ    — temporoparietal junction (social cognition, curiosity)

Matches the heuristic_scorer interface so both can be swapped transparently.
"""

import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    genai = None
    genai_types = None
    _GENAI_AVAILABLE = False


_PROMPT = """You are a content scoring AI. Analyze this video transcript and score it on 4 dimensions (0.0 to 1.0):

- A5 (Auditory Cortex): Pacing, rhythm, vocal clarity. Does the transcript flow naturally? Are there pauses, varied cadence?
- LO (Lateral Occipital): Visual/descriptive language. Does it paint mental pictures? Use vivid, concrete imagery?
- Area45 (Broca's Area): CTA activation, persuasion. Is there a clear call to action? Persuasive framing?
- TPJ (Temporoparietal Junction): Social cognition, curiosity. Does it tap into social dynamics, shared experiences, curiosity gaps?

Return ONLY valid JSON:
{"A5": 0.0, "LO": 0.0, "Area45": 0.0, "TPJ": 0.0, "rationale": "brief explanation of scoring"}

Transcript:
"""


class LLMScorer:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or "gemini-2.0-flash-lite"
        self.enabled = bool(api_key and _GENAI_AVAILABLE and genai is not None)
        if self.enabled:
            self._client = genai.Client(api_key=api_key)

    def score_transcript(self, text: str) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "A5": 0.0,
                "LO": 0.0,
                "Area45": 0.0,
                "TPJ": 0.0,
                "mode": "disabled",
                "word_count": len(text.split()),
                "note": "LLM scorer not enabled — configure GEMINI_API_KEY",
            }

        text = text.strip()
        if not text:
            return {
                "A5": 0.5,
                "LO": 0.5,
                "Area45": 0.5,
                "TPJ": 0.5,
                "mode": "disabled",
                "word_count": 0,
                "note": "empty transcript",
            }

        prompt = _PROMPT + text[:5000]

        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=[prompt],
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
                raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
                raw = raw.strip()
            data = json.loads(raw)
            return {
                "A5": round(float(data.get("A5", 0)), 3),
                "LO": round(float(data.get("LO", 0)), 3),
                "Area45": round(float(data.get("Area45", 0)), 3),
                "TPJ": round(float(data.get("TPJ", 0)), 3),
                "mode": "llm",
                "word_count": len(text.split()),
                "rationale": data.get("rationale", ""),
            }
        except Exception as e:
            logger.warning(f"LLM scoring failed: {e}")
            return {
                "A5": 0.0,
                "LO": 0.0,
                "Area45": 0.0,
                "TPJ": 0.0,
                "mode": "error",
                "word_count": len(text.split()),
                "error": str(e),
            }
