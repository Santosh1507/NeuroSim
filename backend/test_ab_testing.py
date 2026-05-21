"""Tests for A/B Testing module."""

import pytest
from fastapi.testclient import TestClient

from main import app
from storage_adapter import store
from shared_state import require_auth_user

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown():
    store._reset()
    app.dependency_overrides.clear()
    yield
    store._reset()
    app.dependency_overrides.clear()


class TestABTestingRoutes:
    @pytest.mark.asyncio
    async def test_create_ab_test_script_success(self):
        # Override auth dependency to return "anonymous"
        app.dependency_overrides[require_auth_user] = lambda: "anonymous"

        # Seed mock video and analysis
        await store.insert_video("video_1", "baseline.mp4", "analyzed")
        analysis_data = {
            "hook_score": 0.6,
            "hold_rate": 0.5,
            "virality_score": 60,
            "engagement_curve": [0.6, 0.5],
            "brain_regions": {"visual_cortex": 0.6},
        }
        await store.insert_analysis("video_1", analysis_data)

        # Execute creation call
        payload = {
            "name": "Hook Optimizer",
            "baseline_video_id": "video_1",
            "variant_script": "🚨 Attention! This is variant script content.",
        }

        response = client.post("/api/v1/ab-tests", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "Hook Optimizer"
        assert data["results"]["version_a"]["hook_score"] == 0.6
        assert data["results"]["version_b"]["hook_score"] > 0.6  # simulated boost
        assert data["results"]["winner"] == "B"

    @pytest.mark.asyncio
    async def test_create_ab_test_video_success(self):
        app.dependency_overrides[require_auth_user] = lambda: "anonymous"

        # Seed two videos and their analyses
        await store.insert_video("video_a", "baseline.mp4", "analyzed")
        await store.insert_analysis("video_a", {"hook_score": 0.6, "hold_rate": 0.5, "virality_score": 60})

        await store.insert_video("video_b", "variant.mp4", "analyzed")
        await store.insert_analysis("video_b", {"hook_score": 0.8, "hold_rate": 0.7, "virality_score": 80})

        payload = {
            "name": "Baseline vs Variant Video",
            "baseline_video_id": "video_a",
            "variant_video_id": "video_b",
        }

        response = client.post("/api/v1/ab-tests", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["results"]["version_a"]["hook_score"] == 0.6
        assert data["results"]["version_b"]["hook_score"] == 0.8
        assert data["results"]["winner"] == "B"

    @pytest.mark.asyncio
    async def test_list_and_get_ab_tests(self):
        app.dependency_overrides[require_auth_user] = lambda: "user_123"

        # Create one A/B test directly in the cache/database
        test_id = "ab_test_mock"
        results = {"winner": "A"}
        await store.insert_ab_test(
            ab_test_id=test_id,
            name="My AB Test",
            baseline_video_id="video_1",
            variant_video_id="video_2",
            variant_script=None,
            results=results,
            user_id="user_123",
        )

        # Test listing
        response = client.get("/api/v1/ab-tests")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ab_tests"]) == 1
        assert data["ab_tests"][0]["id"] == test_id

        # Test fetching specific A/B test
        response_get = client.get(f"/api/v1/ab-tests/{test_id}")
        assert response_get.status_code == 200
        assert response_get.json()["ab_test"]["id"] == test_id

    @pytest.mark.asyncio
    async def test_delete_ab_test(self):
        app.dependency_overrides[require_auth_user] = lambda: "user_123"

        test_id = "ab_test_delete"
        await store.insert_ab_test(
            ab_test_id=test_id,
            name="To Delete",
            baseline_video_id="video_1",
            variant_video_id=None,
            variant_script="test",
            results={},
            user_id="user_123",
        )

        response = client.delete(f"/api/v1/ab-tests/{test_id}")
        assert response.status_code == 200
        assert await store.get_ab_test(test_id) is None
