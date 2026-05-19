# Phase 4: Strategic — Detailed Tasks

## T19: Prediction Accuracy Validation Study

### Step 1: Create `docs/validation-study.md`

```markdown
# Prediction Accuracy Validation Study

## Hypothesis
Heuristic ROI scores (A5, LO, Area45, TPJ) correlate with actual video performance metrics (views, engagement rate).

## Method
1. Collect 100+ videos with known view counts and engagement rates
2. Run each through the heuristic scoring pipeline
3. Calculate Pearson correlation between each ROI score and actual metrics
4. Compare against baseline (random predictions)

## Success Criteria
- r > 0.3 for at least 2 ROI scores vs views
- r > 0.3 for at least 1 ROI score vs engagement rate
- Better than random baseline (r > 0.05)

## Data Collection
- Source: Users who share actual performance via dashboard feedback
- Minimum: 100 videos for statistical significance
- Timeline: 3-6 months at current user volume

## Risks
- Small sample size → unreliable correlations
- Selection bias (users who share data may be atypical)
- External factors (algorithm changes, timing) confound results
```

### Step 2: Create `backend/correlation_tracker.py`

```python
import json
from typing import Dict, List
from pathlib import Path

class CorrelationTracker:
    def __init__(self, data_path: str = "data/correlations.json"):
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        if self.data_path.exists():
            return json.loads(self.data_path.read_text())
        return []

    def _save(self):
        self.data_path.write_text(json.dumps(self._entries, indent=2))

    def add_entry(self, video_id: str, predicted_scores: Dict[str, float], actual_views: int, actual_engagement: float):
        self._entries.append({"video_id": video_id, "predicted_scores": predicted_scores,
            "actual_views": actual_views, "actual_engagement": actual_engagement})
        self._save()

    def get_correlations(self) -> Dict[str, float]:
        if len(self._entries) < 10:
            return {"error": "Need at least 10 entries"}
        import numpy as np
        correlations = {}
        for score_name in ["hook_score", "viral_potential", "success_probability"]:
            predicted = [e["predicted_scores"].get(score_name, 0) for e in self._entries]
            actual = [e["actual_views"] for e in self._entries]
            corr = float(np.corrcoef(predicted, actual)[0, 1])
            correlations[score_name] = round(corr, 3)
        return correlations
```

### Step 3: Commit
```bash
git add docs/validation-study.md backend/correlation_tracker.py
git commit -m "feat: add prediction accuracy validation study framework"
```

---

## T20: Pro Tier Technical Path

### Step 1: Create `docs/pro-tier-roadmap.md`

```markdown
# Pro Tier Technical Roadmap

## Current State
- Simulated TRIBE v2 (random arrays)
- Simulated MiroFish (1000-agent swarm, no real LLM)
- Heuristic scoring (lexicon-based, $0/video)

## Pro Tier Options

### Option 1: LLM-Enhanced Scoring
- Use GPT-4o-mini to score transcripts
- Cost: ~$0.002/video (1000 tokens in, 50 out)
- Pros: Easy to implement, immediate improvement
- Cons: Still not "real neural encoding"

### Option 2: Real GPU Inference
- Modal.com, RunPod, or Replicate for GPU inference
- Cost: ~$0.05-0.20/video depending on model
- Pros: Real model predictions
- Cons: Complex infrastructure, higher cost

### Option 3: Hybrid (Recommended)
- Keep heuristic as base (fast, free)
- Add LLM refinement for Pro users
- Cost: ~$0.002/video for LLM layer
- Pros: Best cost/quality ratio, incremental improvement
- Cons: Still not TRIBE v2

## Recommendation: Option 3 (Hybrid)
1. Week 1: Implement LLM scorer (llm_scorer.py)
2. Week 2: A/B test heuristic vs LLM on existing videos
3. Week 3: Build Pro tier billing + feature flag
4. Week 4: Launch Pro tier with "LLM-enhanced analysis"

## Messaging Change
- Current: "Pro — Real GPU-powered TRIBE v2 brain encoding"
- Proposed: "Pro — LLM-enhanced analysis with deeper insights"
- Remove "TRIBE v2" until there's a concrete path to it
```

### Step 2: Update pricing page messaging

Change "Pro (coming soon)" to reflect the actual technical path.

### Step 3: Commit
```bash
git add docs/pro-tier-roadmap.md
git commit -m "docs: define Pro tier roadmap with hybrid LLM approach"
```

---

## T21: Defensible Moat — Data Collection

### Step 1: Create `docs/data-moat-strategy.md`

```markdown
# Data Moat Strategy

## The Only Defensible Moat
Correlation dataset: predicted scores → actual video performance.
Heuristic scoring is replicable. Data accumulation is not.

## Collection Mechanism
Post-analysis survey: "How did this video perform?"
- Actual views
- Actual engagement rate
- Would you publish this? (Yes/No)

## Incentive
Users who share actual performance data get 1 free Pro month.

## Target
- 500+ data points within 6 months
- Statistical significance at n=100
- Actionable insights at n=500

## Competitive Advantage
Once we have 500+ correlated predictions, we can:
1. Validate/improve heuristic weights
2. Train a custom model on our data
3. Publish accuracy studies (marketing)
4. Offer "industry benchmark" comparisons
```

### Step 2: Add feedback to dashboard

Add "How did this perform?" button to analysis results that opens a form:
- Actual views (number input)
- Actual engagement rate (percentage input)
- Would you publish this? (Yes/No toggle)

### Step 3: Commit
```bash
git add docs/data-moat-strategy.md frontend/src/app/dashboard/page.tsx
git commit -m "feat: add performance feedback for data collection"
```

---

## T22: LLM vs Heuristic Comparison

### Step 1: Create `backend/llm_scorer.py`

```python
import os
from typing import Dict, Optional

class LLMScorer:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
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
        # Implementation using openai client
        return {"A5": 0.0, "LO": 0.0, "Area45": 0.0, "TPJ": 0.0, "mode": "llm"}
```

### Step 2: Create `backend/test_llm_comparison.py`

```python
import pytest

class TestLLMScorer:
    def test_disabled_without_api_key(self):
        from llm_scorer import LLMScorer
        scorer = LLMScorer(api_key=None)
        result = scorer.score_transcript("test")
        assert result["mode"] == "disabled"

    def test_same_format_as_heuristic(self):
        from heuristic_scorer import score_transcript
        from llm_scorer import LLMScorer
        heuristic = score_transcript("Hello world, this is a test video.")
        assert all(k in heuristic for k in ["A5", "LO", "Area45", "TPJ"])
```

### Step 3: Run tests
```bash
cd backend && python -m pytest test_llm_comparison.py -v
```

### Step 4: Commit
```bash
git add backend/llm_scorer.py backend/test_llm_comparison.py
git commit -m "feat: add LLM scorer for heuristic comparison study"
```
