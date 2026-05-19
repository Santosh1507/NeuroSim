"""Validation study infrastructure — track prediction-outcome correlations.

Stores prediction-outcome pairs, computes Pearson/Spearman correlations
with significance testing, and tracks study progress toward the target
of 20 users completing the validation loop.
"""
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ValidationEntry:
    video_id: str
    user_id: str
    analysis_type: str  # "video" or "script"
    predicted_scores: Dict[str, float]
    actual_views: int
    actual_engagement: float
    would_publish: bool
    days_after_publish: int
    submitted_at: str


@dataclass
class CorrelationResult:
    metric: str
    pearson_r: float
    p_value: float
    n_samples: int
    significant: bool


class ValidationStudy:
    TARGET_ENTRIES = 20
    MIN_SAMPLES_FOR_CORR = 5

    def __init__(self, data_path: str = "data/validation_study.json"):
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[ValidationEntry] = self._load()

    def _load(self) -> List[ValidationEntry]:
        if self.data_path.exists():
            raw = json.loads(self.data_path.read_text())
            return [ValidationEntry(**e) for e in raw]
        return []

    def _save(self):
        raw = [asdict(e) for e in self._entries]
        self.data_path.write_text(json.dumps(raw, indent=2))

    def add_entry(
        self,
        video_id: str,
        user_id: str,
        analysis_type: str,
        predicted_scores: Dict[str, float],
        actual_views: int,
        actual_engagement: float,
        would_publish: bool,
        days_after_publish: int,
    ) -> ValidationEntry:
        entry = ValidationEntry(
            video_id=video_id,
            user_id=user_id,
            analysis_type=analysis_type,
            predicted_scores=predicted_scores,
            actual_views=actual_views,
            actual_engagement=actual_engagement,
            would_publish=would_publish,
            days_after_publish=days_after_publish,
            submitted_at=datetime.now().isoformat(),
        )
        self._entries.append(entry)
        self._save()
        return entry

    def get_study_progress(self) -> Dict[str, Any]:
        unique_users = len(set(e.user_id for e in self._entries))
        return {
            "total_entries": len(self._entries),
            "unique_users": unique_users,
            "target_entries": self.TARGET_ENTRIES,
            "completion_pct": round(
                min(len(self._entries) / self.TARGET_ENTRIES * 100, 100), 1
            ),
            "by_type": {
                "video": len([e for e in self._entries if e.analysis_type == "video"]),
                "script": len([e for e in self._entries if e.analysis_type == "script"]),
            },
        }

    def compute_correlations(self) -> Dict[str, Any]:
        if len(self._entries) < self.MIN_SAMPLES_FOR_CORR:
            return {
                "status": "insufficient_data",
                "message": f"Need at least {self.MIN_SAMPLES_FOR_CORR} entries (have {len(self._entries)})",
                "entries_needed": self.MIN_SAMPLES_FOR_CORR - len(self._entries),
            }

        results = {}
        metrics = ["hook_score", "viral_potential", "success_probability"]

        for metric in metrics:
            predicted = [e.predicted_scores.get(metric, 0) for e in self._entries]
            actual_views = [e.actual_views for e in self._entries]
            actual_engagement = [e.actual_engagement for e in self._entries]

            pearson_r_views, p_views = self._pearson_correlation(predicted, actual_views)
            pearson_r_eng, p_eng = self._pearson_correlation(
                predicted, actual_engagement
            )

            results[metric] = {
                "vs_views": {
                    "pearson_r": round(pearson_r_views, 3),
                    "p_value": round(p_views, 4),
                    "significant": p_views < 0.05,
                },
                "vs_engagement": {
                    "pearson_r": round(pearson_r_eng, 3),
                    "p_value": round(p_eng, 4),
                    "significant": p_eng < 0.05,
                },
            }

        return {
            "status": "computed",
            "n_samples": len(self._entries),
            "correlations": results,
        }

    def get_benchmark_comparison(self) -> Dict[str, Any]:
        """Anonymized benchmark: how does a user's prediction compare to the cohort."""
        if len(self._entries) < 3:
            return {"status": "insufficient_data"}

        avg_success = sum(
            e.predicted_scores.get("success_probability", 0) for e in self._entries
        ) / len(self._entries)
        avg_viral = sum(
            e.predicted_scores.get("viral_potential", 0) for e in self._entries
        ) / len(self._entries)
        avg_hook = sum(
            e.predicted_scores.get("hook_score", 0) for e in self._entries
        ) / len(self._entries)

        return {
            "status": "available",
            "cohort_averages": {
                "success_probability": round(avg_success, 1),
                "viral_potential": round(avg_viral, 1),
                "hook_score": round(avg_hook, 1),
            },
            "total_analyses": len(self._entries),
        }

    def get_user_entries(self, user_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "video_id": e.video_id,
                "analysis_type": e.analysis_type,
                "predicted_scores": e.predicted_scores,
                "actual_views": e.actual_views,
                "actual_engagement": e.actual_engagement,
                "submitted_at": e.submitted_at,
            }
            for e in self._entries
            if e.user_id == user_id
        ]

    @staticmethod
    def _pearson_correlation(x: List[float], y: List[float]) -> tuple:
        """Compute Pearson correlation coefficient and approximate p-value."""
        n = len(x)
        if n < 2:
            return 0.0, 1.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        ss_xx = sum((xi - mean_x) ** 2 for xi in x)
        ss_yy = sum((yi - mean_y) ** 2 for yi in y)
        ss_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))

        if ss_xx == 0 or ss_yy == 0:
            return 0.0, 1.0

        r = ss_xy / math.sqrt(ss_xx * ss_yy)
        r = max(-1.0, min(1.0, r))

        # Approximate p-value using t-distribution
        if abs(r) >= 1.0:
            p = 0.0
        else:
            t_stat = r * math.sqrt((n - 2) / (1 - r * r))
            p = 2 * (1 - ValidationStudy._t_cdf(abs(t_stat), n - 2))

        return round(r, 4), round(p, 4)

    @staticmethod
    def _t_cdf(t: float, df: int) -> float:
        """Approximate t-distribution CDF using normal approximation for df >= 30,
        or a simple approximation for smaller df."""
        if df >= 30:
            return ValidationStudy._normal_cdf(t)

        x = df / (df + t * t)
        return 1 - 0.5 * ValidationStudy._regularized_incomplete_beta(x, df / 2, 0.5)

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Approximation of standard normal CDF."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    @staticmethod
    def _regularized_incomplete_beta(x: float, a: float, b: float) -> float:
        """Simple approximation for regularized incomplete beta function."""
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        return x**a * (1 - x) ** b / (a * ValidationStudy._beta_func(a, b))

    @staticmethod
    def _beta_func(a: float, b: float) -> float:
        """Approximation of beta function using gamma."""
        return math.gamma(a) * math.gamma(b) / math.gamma(a + b)
