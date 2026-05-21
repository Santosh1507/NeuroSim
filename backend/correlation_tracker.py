"""Correlation tracker for prediction accuracy validation study.

Stores predicted scores vs actual video performance and computes
Pearson correlations. JSON-backed — no database dependency, free to run.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class CorrelationTracker:
    """Tracks predicted scores vs actual performance and computes correlations."""

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

    def add_entry(
        self,
        video_id: str,
        predicted_scores: Dict[str, float],
        actual_views: int,
        actual_engagement: float,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Add a prediction-vs-actual data point."""
        self._entries.append({
            "video_id": video_id,
            "predicted_scores": predicted_scores,
            "actual_views": actual_views,
            "actual_engagement": actual_engagement,
            "metadata": metadata or {},
        })
        self._save()

    def count(self) -> int:
        return len(self._entries)

    def get_entries(self) -> List[Dict]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._save()

    def get_correlations(self) -> Dict:
        """Compute Pearson correlations between predicted scores and actual views.

        Returns a dict with correlation coefficients for each score dimension,
        or an error message if insufficient data (< 10 entries).
        """
        if len(self._entries) < 10:
            return {
                "error": f"Need at least 10 entries (have {len(self._entries)})",
                "entries_count": len(self._entries),
                "minimum_required": 10,
            }

        try:
            import numpy as np

            correlations = {}
            score_names = ["hook_score", "viral_potential", "success_probability", "risk_score"]

            for score_name in score_names:
                predicted = [
                    e["predicted_scores"].get(score_name, 0)
                    for e in self._entries
                ]
                actual = [e["actual_views"] for e in self._entries]

                if len(set(predicted)) < 2 or len(set(actual)) < 2:
                    correlations[score_name] = None
                    continue

                corr = float(np.corrcoef(predicted, actual)[0, 1])
                correlations[score_name] = round(corr, 3)

            # Also compute vs engagement rate
            engagement_corrs = {}
            for score_name in score_names:
                predicted = [
                    e["predicted_scores"].get(score_name, 0)
                    for e in self._entries
                ]
                actual = [e["actual_engagement"] for e in self._entries]

                if len(set(predicted)) < 2 or len(set(actual)) < 2:
                    engagement_corrs[score_name] = None
                    continue

                corr = float(np.corrcoef(predicted, actual)[0, 1])
                engagement_corrs[score_name] = round(corr, 3)

            return {
                "entries_count": len(self._entries),
                "vs_views": correlations,
                "vs_engagement": engagement_corrs,
                "random_baseline": 0.05,
                "success_threshold": 0.3,
            }

        except ImportError:
            return {
                "error": "numpy not installed — install with: pip install numpy",
                "entries_count": len(self._entries),
            }


# Singleton for app-wide use
correlation_tracker = CorrelationTracker()
