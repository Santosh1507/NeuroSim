"""
Heuristic Neural Scorer
Uses LLM to estimate ROI proxy scores (A5, LO, Area45, TPJ) from video transcript and metadata.
Replaces TRIBE v2 for MVP — no GPU required.
"""

import json
import re
from typing import Dict, Any, Optional

from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger('mirofish.heuristic_scorer')


class HeuristicScorer:
    """Estimates neural ROI scores from content using LLM analysis."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def score_content(
        self,
        transcript: str,
        frame_count: int = 0,
        duration_seconds: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Analyze content and estimate ROI proxy scores.

        Args:
            transcript: Video transcript text.
            frame_count: Number of extracted frames.
            duration_seconds: Video duration in seconds.

        Returns:
            Dict with ROI scores (A5, LO, Area45, TPJ) each 0.0-1.0, plus reasoning.
        """
        if not transcript or len(transcript.strip()) < 10:
            return self._default_scores("No transcript available")

        prompt = self._build_prompt(transcript, frame_count, duration_seconds)

        try:
            result = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": "You are a neural response prediction expert. Return pure JSON with ROI scores between 0.0 and 1.0."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1024,
            )

            scores = self._parse_scores(result)
            reasoning = result.get('reasoning', 'LLM analysis complete')

            logger.info(f"Heuristic scoring complete: A5={scores['A5']:.2f}, LO={scores['LO']:.2f}, Area45={scores['Area45']:.2f}, TPJ={scores['TPJ']:.2f}")

            return {
                'A5': scores['A5'],
                'LO': scores['LO'],
                'Area45': scores['Area45'],
                'TPJ': scores['TPJ'],
                'reasoning': reasoning,
                'model_used': self.llm.model,
            }

        except Exception as e:
            logger.warning(f"Heuristic scoring failed: {e}, using default scores")
            return self._default_scores(f"Scoring failed: {str(e)}")

    def _build_prompt(self, transcript: str, frame_count: int, duration: float) -> str:
        """Build LLM prompt for ROI estimation."""
        # Truncate transcript if too long
        max_len = 8000
        transcript_preview = transcript[:max_len]
        if len(transcript) > max_len:
            transcript_preview += "\n...(truncated)"

        return f"""Analyze the following video content and estimate neural activation scores for 4 brain regions of interest (ROIs).

## Video Metadata
- Duration: {duration:.1f} seconds
- Frame count: {frame_count} frames extracted

## Transcript
{transcript_preview}

## Task
Estimate activation scores (0.0 to 1.0) for these 4 ROIs:

1. **A5 (Auditory Attention)**: How engaging is the audio/speech? Does it capture and hold attention?
   - High scores: compelling narrative, dynamic pacing, emotional vocal delivery
   - Low scores: monotone, repetitive, confusing audio

2. **LO (Visual Composition)**: How visually striking is the content?
   - High scores: strong visual hooks, dynamic scenes, professional composition
   - Low scores: static visuals, poor framing, bland imagery

3. **Area45 (Valuation/Reward)**: How rewarding/valuable does the content feel?
   - High scores: clear value proposition, emotional payoff, satisfying conclusion
   - Low scores: unclear purpose, no payoff, feels like wasted time

4. **TPJ (Temporoparietal Junction - Social Cognition)**: How socially engaging is the content?
   - High scores: relatable characters, social dynamics, empathy triggers
   - Low scores: impersonal, abstract, no social connection

## Return JSON format (no markdown)
{{
    "A5": 0.0-1.0,
    "LO": 0.0-1.0,
    "Area45": 0.0-1.0,
    "TPJ": 0.0-1.0,
    "reasoning": "Brief explanation of scores based on content analysis"
}}"""

    def _parse_scores(self, result: Dict[str, Any]) -> Dict[str, float]:
        """Parse and validate ROI scores from LLM response."""
        scores = {}
        for key in ['A5', 'LO', 'Area45', 'TPJ']:
            val = result.get(key, 0.5)
            try:
                val = float(val)
            except (ValueError, TypeError):
                val = 0.5
            scores[key] = max(0.0, min(1.0, val))
        return scores

    def _default_scores(self, reason: str) -> Dict[str, Any]:
        """Return default neutral scores with reason."""
        return {
            'A5': 0.5,
            'LO': 0.5,
            'Area45': 0.5,
            'TPJ': 0.5,
            'reasoning': reason,
            'model_used': 'default',
        }
