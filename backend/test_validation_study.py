"""Tests for validation study infrastructure."""
import pytest
from validation_study import ValidationStudy, ValidationEntry


class _MockStore:
    """Minimal in-memory store for testing ValidationStudy with store backend."""

    def __init__(self):
        self.entries: list[dict] = []

    async def insert_validation_entry(self, entry: dict) -> dict:
        self.entries.append(entry)
        return entry

    async def list_validation_entries(self) -> list[dict]:
        return list(self.entries)

    async def delete_validation_entry(self, entry_id: str) -> None:
        self.entries[:] = [e for e in self.entries if e.get("id") != entry_id]

    def clear(self):
        self.entries.clear()


@pytest.fixture(autouse=True)
def clean_study(tmp_path):
    """Use a temp file for each test to avoid cross-test pollution."""
    data_file = tmp_path / "validation_study.json"
    return ValidationStudy(str(data_file))


@pytest.fixture
def store_study(tmp_path):
    """Use a mock store backend to test store-based persistence."""
    mock_store = _MockStore()
    data_file = tmp_path / "validation_study.json"
    return ValidationStudy(str(data_file), store=mock_store), mock_store


class TestValidationStudyStoreBackend:
    """Tests that verify store-backed persistence works correctly."""

    @pytest.mark.asyncio
    async def test_store_backed_add_entry(self, store_study):
        study, mock_store = store_study
        entry = await study.add_entry(
            video_id="v1",
            user_id="user1",
            analysis_type="video",
            predicted_scores={"hook_score": 70, "viral_potential": 60, "success_probability": 65},
            actual_views=1000,
            actual_engagement=5.0,
            would_publish=True,
            days_after_publish=7,
        )
        assert len(mock_store.entries) == 1
        assert mock_store.entries[0]["video_id"] == "v1"
        assert study.get_study_progress()["total_entries"] == 1

    @pytest.mark.asyncio
    async def test_store_backed_multiple_entries(self, store_study):
        study, mock_store = store_study
        for i in range(5):
            await study.add_entry(
                video_id=f"v{i}",
                user_id=f"user{i}",
                analysis_type="video",
                predicted_scores={"hook_score": 70, "viral_potential": 60, "success_probability": 65},
                actual_views=1000,
                actual_engagement=5.0,
                would_publish=True,
                days_after_publish=7,
            )
        assert len(mock_store.entries) == 5
        assert study.get_study_progress()["total_entries"] == 5

    @pytest.mark.asyncio
    async def test_store_fallback_on_file(self, store_study):
        """When store is available, file should NOT be written (store is primary)."""
        study, mock_store = store_study
        await study.add_entry(
            video_id="v1",
            user_id="user1",
            analysis_type="video",
            predicted_scores={"hook_score": 70, "viral_potential": 60, "success_probability": 65},
            actual_views=1000,
            actual_engagement=5.0,
            would_publish=True,
            days_after_publish=7,
        )
        # Since store succeeded, the JSON file should not exist
        assert not study.data_path.exists()

    @pytest.mark.asyncio
    async def test_store_backed_correlations(self, store_study):
        study, mock_store = store_study
        for i in range(10):
            await study.add_entry(
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
        result = study.compute_correlations()
        assert result["status"] == "computed"
        assert result["n_samples"] == 10

    @pytest.mark.asyncio
    async def test_store_does_not_affect_in_memory_computation(self, store_study):
        """Store failure should not corrupt in-memory state."""
        study, mock_store = store_study
        await study.add_entry(
            video_id="v1",
            user_id="user1",
            analysis_type="video",
            predicted_scores={"hook_score": 70, "viral_potential": 60, "success_probability": 65},
            actual_views=1000,
            actual_engagement=5.0,
            would_publish=True,
            days_after_publish=7,
        )
        mock_store.clear()
        # In-memory state should survive store clearing
        assert study.get_study_progress()["total_entries"] == 1


class TestValidationStudyProgress:
    def test_empty_study(self, clean_study):
        progress = clean_study.get_study_progress()
        assert progress["total_entries"] == 0
        assert progress["unique_users"] == 0
        assert progress["completion_pct"] == 0.0

    @pytest.mark.asyncio
    async def test_single_entry(self, clean_study):
        await clean_study.add_entry(
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

    @pytest.mark.asyncio
    async def test_multiple_users(self, clean_study):
        for i in range(5):
            await clean_study.add_entry(
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

    @pytest.mark.asyncio
    async def test_correlation_with_enough_data(self, clean_study):
        for i in range(10):
            await clean_study.add_entry(
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

    @pytest.mark.asyncio
    async def test_correlation_structure(self, clean_study):
        for i in range(5):
            await clean_study.add_entry(
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

    @pytest.mark.asyncio
    async def test_benchmark_available(self, clean_study):
        for i in range(5):
            await clean_study.add_entry(
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
    @pytest.mark.asyncio
    async def test_get_user_entries(self, clean_study):
        await clean_study.add_entry(
            video_id="v1",
            user_id="alice",
            analysis_type="script",
            predicted_scores={"hook_score": 80, "viral_potential": 70, "success_probability": 75},
            actual_views=2000,
            actual_engagement=6.0,
            would_publish=True,
            days_after_publish=7,
        )
        await clean_study.add_entry(
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
