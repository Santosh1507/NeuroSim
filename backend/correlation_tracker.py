"""Track predicted vs actual video performance for validation studies."""
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
        self._entries.append({
            "video_id": video_id,
            "predicted_scores": predicted_scores,
            "actual_views": actual_views,
            "actual_engagement": actual_engagement,
        })
        self._save()

    def get_correlations(self) -> Dict[str, float]:
        if len(self._entries) < 10:
            return {"error": "Need at least 10 entries"}
        try:
            import numpy as np
        except ImportError:
            return {"error": "numpy not installed"}
        correlations = {}
        for score_name in ["hook_score", "viral_potential", "success_probability"]:
            predicted = [e["predicted_scores"].get(score_name, 0) for e in self._entries]
            actual = [e["actual_views"] for e in self._entries]
            corr = float(np.corrcoef(predicted, actual)[0, 1])
            correlations[score_name] = round(corr, 3)
        return correlations

    def entry_count(self) -> int:
        return len(self._entries)
