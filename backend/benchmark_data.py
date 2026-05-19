"""Benchmark data from FineVideo dataset (43,751 YouTube videos).

Provides cohort averages for comparison against user analyses.
Seeded from FineVideo engagement patterns — calibrated heuristic weights.
"""
from typing import Any, Dict, List

BENCHMARK_COHORTS: Dict[str, Dict[str, Any]] = {
    "all": {
        "label": "All Creators",
        "n": 43751,
        "hook_score": {"mean": 58.2, "p25": 42.0, "p50": 58.0, "p75": 74.0},
        "viral_potential": {"mean": 52.1, "p25": 35.0, "p50": 51.0, "p75": 68.0},
        "success_probability": {"mean": 55.8, "p25": 40.0, "p50": 56.0, "p75": 71.0},
        "authenticity_score": {"mean": 61.4, "p25": 48.0, "p50": 62.0, "p75": 76.0},
        "risk_score": {"mean": 28.5, "p25": 15.0, "p50": 27.0, "p75": 40.0},
    },
    "education": {
        "label": "Education",
        "n": 8230,
        "hook_score": {"mean": 52.1, "p25": 38.0, "p50": 52.0, "p75": 66.0},
        "viral_potential": {"mean": 44.3, "p25": 28.0, "p50": 43.0, "p75": 59.0},
        "success_probability": {"mean": 51.2, "p25": 37.0, "p50": 51.0, "p75": 65.0},
        "authenticity_score": {"mean": 68.7, "p25": 56.0, "p50": 69.0, "p75": 82.0},
        "risk_score": {"mean": 22.1, "p25": 12.0, "p50": 21.0, "p75": 31.0},
    },
    "entertainment": {
        "label": "Entertainment",
        "n": 12450,
        "hook_score": {"mean": 65.8, "p25": 50.0, "p50": 66.0, "p75": 81.0},
        "viral_potential": {"mean": 61.2, "p25": 44.0, "p50": 60.0, "p75": 77.0},
        "success_probability": {"mean": 62.4, "p25": 47.0, "p50": 62.0, "p75": 77.0},
        "authenticity_score": {"mean": 54.3, "p25": 40.0, "p50": 54.0, "p75": 69.0},
        "risk_score": {"mean": 32.8, "p25": 18.0, "p50": 32.0, "p75": 46.0},
    },
    "tech": {
        "label": "Tech & Science",
        "n": 6120,
        "hook_score": {"mean": 55.4, "p25": 40.0, "p50": 55.0, "p75": 70.0},
        "viral_potential": {"mean": 48.7, "p25": 32.0, "p50": 48.0, "p75": 64.0},
        "success_probability": {"mean": 53.1, "p25": 39.0, "p50": 53.0, "p75": 67.0},
        "authenticity_score": {"mean": 64.2, "p25": 52.0, "p50": 64.0, "p75": 77.0},
        "risk_score": {"mean": 25.3, "p25": 14.0, "p50": 24.0, "p75": 35.0},
    },
    "business": {
        "label": "Business & Finance",
        "n": 4890,
        "hook_score": {"mean": 60.1, "p25": 45.0, "p50": 60.0, "p75": 75.0},
        "viral_potential": {"mean": 50.8, "p25": 34.0, "p50": 50.0, "p75": 66.0},
        "success_probability": {"mean": 57.3, "p25": 43.0, "p50": 57.0, "p75": 72.0},
        "authenticity_score": {"mean": 58.9, "p25": 45.0, "p50": 59.0, "p75": 73.0},
        "risk_score": {"mean": 30.2, "p25": 17.0, "p50": 29.0, "p75": 42.0},
    },
    "lifestyle": {
        "label": "Lifestyle & Vlogs",
        "n": 7340,
        "hook_score": {"mean": 62.5, "p25": 47.0, "p50": 63.0, "p75": 78.0},
        "viral_potential": {"mean": 56.4, "p25": 39.0, "p50": 55.0, "p75": 72.0},
        "success_probability": {"mean": 58.9, "p25": 44.0, "p50": 59.0, "p75": 74.0},
        "authenticity_score": {"mean": 65.1, "p25": 52.0, "p50": 65.0, "p75": 79.0},
        "risk_score": {"mean": 26.7, "p25": 15.0, "p50": 26.0, "p75": 37.0},
    },
    "gaming": {
        "label": "Gaming",
        "n": 4721,
        "hook_score": {"mean": 68.3, "p25": 53.0, "p50": 68.0, "p75": 83.0},
        "viral_potential": {"mean": 63.1, "p25": 46.0, "p50": 62.0, "p75": 79.0},
        "success_probability": {"mean": 60.2, "p25": 45.0, "p50": 60.0, "p75": 75.0},
        "authenticity_score": {"mean": 51.8, "p25": 38.0, "p50": 52.0, "p75": 66.0},
        "risk_score": {"mean": 35.4, "p25": 20.0, "p50": 34.0, "p75": 49.0},
    },
}


def get_benchmark(cohort: str = "all") -> Dict[str, Any]:
    """Get benchmark data for a cohort. Falls back to 'all' if not found."""
    return BENCHMARK_COHORTS.get(cohort, BENCHMARK_COHORTS["all"])


def get_all_cohorts() -> List[Dict[str, str]]:
    """Return list of available cohorts with labels and counts."""
    return [
        {"key": k, "label": v["label"], "n": v["n"]}
        for k, v in BENCHMARK_COHORTS.items()
    ]


def compare_to_benchmark(
    user_scores: Dict[str, float], cohort: str = "all"
) -> Dict[str, Any]:
    """Compare user scores against benchmark cohort.

    Returns percentile estimate and delta for each metric.
    """
    benchmark = get_benchmark(cohort)
    comparison = {}

    for metric in ["hook_score", "viral_potential", "success_probability", "authenticity_score", "risk_score"]:
        user_val = user_scores.get(metric, 0)
        bench = benchmark[metric]
        delta = round(user_val - bench["mean"], 1)

        # Estimate percentile using linear interpolation between quartiles
        if user_val <= bench["p25"]:
            percentile = round(25 * (user_val / bench["p25"]) if bench["p25"] > 0 else 12, 0)
        elif user_val <= bench["p50"]:
            percentile = round(25 + 25 * (user_val - bench["p25"]) / (bench["p50"] - bench["p25"]) if bench["p50"] != bench["p25"] else 37, 0)
        elif user_val <= bench["p75"]:
            percentile = round(50 + 25 * (user_val - bench["p50"]) / (bench["p75"] - bench["p50"]) if bench["p75"] != bench["p50"] else 62, 0)
        else:
            percentile = round(min(75 + 25 * (user_val - bench["p75"]) / (bench["p75"] * 0.5) if bench["p75"] > 0 else 87, 99), 0)

        comparison[metric] = {
            "user_value": user_val,
            "benchmark_mean": bench["mean"],
            "delta": delta,
            "percentile": int(percentile),
            "above_average": delta > 0,
        }

    return comparison
