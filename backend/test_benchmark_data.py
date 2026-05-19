"""Tests for benchmark data and comparison."""
import pytest
from benchmark_data import get_benchmark, get_all_cohorts, compare_to_benchmark


class TestBenchmarkData:
    def test_get_benchmark_all(self):
        bench = get_benchmark("all")
        assert bench["label"] == "All Creators"
        assert bench["n"] == 43751
        assert "hook_score" in bench

    def test_get_benchmark_cohort(self):
        bench = get_benchmark("education")
        assert bench["label"] == "Education"
        assert bench["n"] == 8230

    def test_get_benchmark_fallback(self):
        bench = get_benchmark("nonexistent")
        assert bench["label"] == "All Creators"

    def test_get_all_cohorts(self):
        cohorts = get_all_cohorts()
        assert len(cohorts) == 7
        assert all("key" in c and "label" in c and "n" in c for c in cohorts)


class TestCompareToBenchmark:
    def test_above_average(self):
        scores = {
            "hook_score": 80,
            "viral_potential": 70,
            "success_probability": 75,
            "authenticity_score": 80,
            "risk_score": 10,
        }
        result = compare_to_benchmark(scores, "all")
        assert result["hook_score"]["above_average"] is True
        assert result["hook_score"]["delta"] > 0
        assert result["hook_score"]["percentile"] > 75

    def test_below_average(self):
        scores = {
            "hook_score": 30,
            "viral_potential": 25,
            "success_probability": 30,
            "authenticity_score": 35,
            "risk_score": 50,
        }
        result = compare_to_benchmark(scores, "all")
        assert result["hook_score"]["above_average"] is False
        assert result["hook_score"]["delta"] < 0
        assert result["hook_score"]["percentile"] < 25

    def test_percentile_structure(self):
        scores = {
            "hook_score": 58,
            "viral_potential": 52,
            "success_probability": 56,
            "authenticity_score": 61,
            "risk_score": 28,
        }
        result = compare_to_benchmark(scores, "all")
        for metric in scores:
            assert "user_value" in result[metric]
            assert "benchmark_mean" in result[metric]
            assert "delta" in result[metric]
            assert "percentile" in result[metric]
            assert "above_average" in result[metric]

    def test_cohort_specific(self):
        scores = {
            "hook_score": 60,
            "viral_potential": 50,
            "success_probability": 55,
            "authenticity_score": 65,
            "risk_score": 25,
        }
        all_result = compare_to_benchmark(scores, "all")
        gaming_result = compare_to_benchmark(scores, "gaming")
        assert all_result["hook_score"]["benchmark_mean"] != gaming_result["hook_score"]["benchmark_mean"]
