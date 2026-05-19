"""Tests for validation study infrastructure."""
import pytest
from validation_study import ValidationStudy, ValidationEntry


@pytest.fixture(autouse=True)
def clean_study(tmp_path):
    """Use a temp file for each test to avoid cross-test pollution."""
    data_file = tmp_path / "validation_study.json"
    return ValidationStudy(str(data_file))


class TestValidationStudyProgress:
    def test_empty_study(self, clean_study):
        progress = clean_study.get_study_progress()
        assert progress["total_entries"] == 0
        assert progress["unique_users"] == 0
        assert progress["completion_pct"] == 0.0

    def test_single_entry(self, clean_study):
        clean_study.add_entry(
            video_id="v1",
            user_id="user1",
            analysis_type="video",
            predicted_scores={"hook_score": 70, "viral_potential": 60, "success_probability": 65},
            actual_views=1000,
            actual_engagement=5.0,
            would_publish=True,
            days_after_publish=7,
        )
        progress = clean_study.get_study_progress()
        assert progress["total_entries"] == 1
        assert progress["unique_users"] == 1
        assert progress["by_type"]["video"] == 1
        assert progress["by_type"]["script"] == 0

    def test_multiple_users(self, clean_study):
        for i in range(5):
            clean_study.add_entry(
                video_id=f"v{i}",
                user_id=f"user{i % 3}",
                analysis_type="video" if i % 2 == 0 else "script",
                predicted_scores={"hook_score": 70, "viral_potential": 60, "success_probability": 65},
                actual_views=1000 * (i + 1),
                actual_engagement=5.0,
                would_publish=True,
                days_after_publish=7,
            )
        progress = clean_study.get_study_progress()
        assert progress["total_entries"] == 5
        assert progress["unique_users"] == 3
        assert progress["by_type"]["video"] == 3
        assert progress["by_type"]["script"] == 2


class TestValidationStudyCorrelations:
    def test_insufficient_data(self, clean_study):
        result = clean_study.compute_correlations()
        assert result["status"] == "insufficient_data"
        assert "entries_needed" in result

    def test_correlation_with_enough_data(self, clean_study):
        for i in range(10):
            clean_study.add_entry(
                video_id=f"v{i}",
                user_id=f"user{i}",
                analysis_type="video",
                predicted_scores={
                    "hook_score": 50 + i * 5,
                    "viral_potential": 40 + i * 3,
                    "success_probability": 60 + i * 2,
                },
                actual_views=1000 + i * 500,
                actual_engagement=3.0 + i * 0.5,
                would_publish=True,
                days_after_publish=7,
            )
        result = clean_study.compute_correlations()
        assert result["status"] == "computed"
        assert result["n_samples"] == 10
        assert "hook_score" in result["correlations"]
        assert "viral_potential" in result["correlations"]
        assert "success_probability" in result["correlations"]

    def test_correlation_structure(self, clean_study):
        for i in range(5):
            clean_study.add_entry(
                video_id=f"v{i}",
                user_id=f"user{i}",
                analysis_type="video",
                predicted_scores={
                    "hook_score": 50 + i * 10,
                    "viral_potential": 40 + i * 10,
                    "success_probability": 60 + i * 10,
                },
                actual_views=1000 + i * 1000,
                actual_engagement=3.0 + i * 1.0,
                would_publish=True,
                days_after_publish=7,
            )
        result = clean_study.compute_correlations()
        hook = result["correlations"]["hook_score"]
        assert "vs_views" in hook
        assert "vs_engagement" in hook
        assert "pearson_r" in hook["vs_views"]
        assert "p_value" in hook["vs_views"]
        assert "significant" in hook["vs_views"]


class TestValidationStudyBenchmarks:
    def test_insufficient_benchmark_data(self, clean_study):
        result = clean_study.get_benchmark_comparison()
        assert result["status"] == "insufficient_data"

    def test_benchmark_available(self, clean_study):
        for i in range(5):
            clean_study.add_entry(
                video_id=f"v{i}",
                user_id=f"user{i}",
                analysis_type="video",
                predicted_scores={
                    "hook_score": 70,
                    "viral_potential": 60,
                    "success_probability": 65,
                },
                actual_views=1000,
                actual_engagement=5.0,
                would_publish=True,
                days_after_publish=7,
            )
        result = clean_study.get_benchmark_comparison()
        assert result["status"] == "available"
        assert result["cohort_averages"]["success_probability"] == 65.0
        assert result["cohort_averages"]["viral_potential"] == 60.0
        assert result["cohort_averages"]["hook_score"] == 70.0
        assert result["total_analyses"] == 5


class TestValidationStudyUserEntries:
    def test_get_user_entries(self, clean_study):
        clean_study.add_entry(
            video_id="v1",
            user_id="alice",
            analysis_type="script",
            predicted_scores={"hook_score": 80, "viral_potential": 70, "success_probability": 75},
            actual_views=2000,
            actual_engagement=6.0,
            would_publish=True,
            days_after_publish=7,
        )
        clean_study.add_entry(
            video_id="v2",
            user_id="bob",
            analysis_type="video",
            predicted_scores={"hook_score": 50, "viral_potential": 40, "success_probability": 45},
            actual_views=500,
            actual_engagement=2.0,
            would_publish=False,
            days_after_publish=14,
        )
        alice_entries = clean_study.get_user_entries("alice")
        bob_entries = clean_study.get_user_entries("bob")

        assert len(alice_entries) == 1
        assert alice_entries[0]["video_id"] == "v1"
        assert alice_entries[0]["analysis_type"] == "script"

        assert len(bob_entries) == 1
        assert bob_entries[0]["video_id"] == "v2"
        assert bob_entries[0]["analysis_type"] == "video"


class TestPearsonCorrelation:
    def test_perfect_positive_correlation(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 20.0, 30.0, 40.0, 50.0]
        r, p = ValidationStudy._pearson_correlation(x, y)
        assert abs(r - 1.0) < 0.001
        assert p < 0.05

    def test_perfect_negative_correlation(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [50.0, 40.0, 30.0, 20.0, 10.0]
        r, p = ValidationStudy._pearson_correlation(x, y)
        assert abs(r - (-1.0)) < 0.001
        assert p < 0.05

    def test_no_correlation(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 5.0, 5.0, 5.0, 5.0]
        r, p = ValidationStudy._pearson_correlation(x, y)
        assert r == 0.0
        assert p == 1.0

    def test_empty_input(self):
        r, p = ValidationStudy._pearson_correlation([], [])
        assert r == 0.0
        assert p == 1.0
