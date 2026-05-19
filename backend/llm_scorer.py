"""LLM-based video transcript scoring for comparison with heuristic scorer."""
import os
from typing import Dict, Optional


class LLMScorer:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, use_env: bool = True):
        if api_key is not None:
            self.api_key = api_key
        elif use_env:
            self.api_key = os.environ.get("OPENAI_API_KEY")
        else:
            self.api_key = None
        self.base_url = base_url or "https://api.openai.com/v1"
        self.enabled = bool(self.api_key)

    def score_transcript(self, transcript: str) -> Dict:
        if not self.enabled:
            return {"error": "LLM scoring not enabled", "mode": "disabled"}

        prompt = f"""Analyze this video transcript and score (0.0 to 1.0):
- A5: Pacing and rhythm
- LO: Visual language
- Area45: Call-to-action strength
- TPJ: Social engagement
Return ONLY JSON: {{"A5": 0.0, "LO": 0.0, "Area45": 0.0, "TPJ": 0.0, "word_count": 0}}

Transcript:
{transcript[:5000]}
"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=200,
            )
            import json
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": str(e), "mode": "error"}
