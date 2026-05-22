"""Unit tests for the Social Feed Simulator routing and algorithmic engine."""

import pytest
from fastapi.testclient import TestClient

from main import app
from shared_state import get_verified_user_id
from storage_adapter import store

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown():
    store._reset()
    app.dependency_overrides.clear()
    yield
    store._reset()
    app.dependency_overrides.clear()


class TestSocialFeedSimulator:
    @pytest.mark.asyncio
    async def test_tiktok_algorithmic_retention(self):
        # 1. Override auth to return a standard user
        app.dependency_overrides[get_verified_user_id] = lambda: "test-user-1"

        # 2. Seed video and high auditory cortex analysis
        video_id = "tiktok_vid"
        await store.insert_video(video_id, "tiktok.mp4", "analyzed")
        analysis_data = {
            "hook_score": 85.0,
            "success_probability": 80.0,
            "engagement_curve": [0.85, 0.82, 0.75, 0.72, 0.70],
            "analysis_response": {
                "cortical_response": {
                    "auditory_cortex": 92.0,  # strong auditory trigger
                    "visual_cortex": 80.0,
                    "amygdala": 70.0,
                }
            }
        }
        await store.insert_analysis(video_id, analysis_data)

        # 3. Simulate TikTok feed
        payload = {
            "video_id": video_id,
            "platform": "tiktok",
            "sound_trend_factor": 0.8,
        }
        response = client.post("/api/v1/simulation/social-feed", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["platform"] == "tiktok"
        assert data["algorithmic_score"] > 70.0
        assert data["vtr"] > 0.6
        assert data["retention_data"]["loop_count"] > 1.5  # high auditory trigger boosts loop count

        # 4. Seed another video with poor auditory score & hook
        video_id_poor = "tiktok_poor_vid"
        await store.insert_video(video_id_poor, "tiktok_poor.mp4", "analyzed")
        analysis_data_poor = {
            "hook_score": 30.0,
            "success_probability": 40.0,
            "engagement_curve": [0.30, 0.25, 0.20, 0.15, 0.10],  # first 2s average < 40%
            "analysis_response": {
                "cortical_response": {
                    "auditory_cortex": 25.0,  # weak auditory trigger
                    "visual_cortex": 30.0,
                    "amygdala": 30.0,
                }
            }
        }
        await store.insert_analysis(video_id_poor, analysis_data_poor)

        payload_poor = {
            "video_id": video_id_poor,
            "platform": "tiktok",
            "sound_trend_factor": 0.5,
        }
        response_poor = client.post("/api/v1/simulation/social-feed", json=payload_poor)
        assert response_poor.status_code == 200
        data_poor = response_poor.json()

        # Low hook (first 2s < 40%) triggers early exponential drop-off alerts
        assert data_poor["retention_data"]["loop_count"] < data["retention_data"]["loop_count"]
        # Ensure drop-off alerts exist for low hook
        assert len(data_poor["retention_data"]["alerts"]) > 0
        assert any(a["severity"] in ("high", "critical") for a in data_poor["retention_data"]["alerts"])

    @pytest.mark.asyncio
    async def test_shorts_vtr_selection(self):
        app.dependency_overrides[get_verified_user_id] = lambda: "test-user-1"

        # Strong hook and high visual cortex vs low hook and low visual cortex
        video_good = "shorts_good"
        await store.insert_video(video_good, "good.mp4", "analyzed")
        await store.insert_analysis(video_good, {
            "hook_score": 90.0,
            "success_probability": 85.0,
            "analysis_response": {
                "cortical_response": {
                    "visual_cortex": 95.0,
                    "auditory_cortex": 60.0,
                    "amygdala": 50.0,
                }
            }
        })

        video_bad = "shorts_bad"
        await store.insert_video(video_bad, "bad.mp4", "analyzed")
        await store.insert_analysis(video_bad, {
            "hook_score": 25.0,
            "success_probability": 30.0,
            "analysis_response": {
                "cortical_response": {
                    "visual_cortex": 20.0,
                    "auditory_cortex": 30.0,
                    "amygdala": 40.0,
                }
            }
        })

        # Test high hook
        res_good = client.post("/api/v1/simulation/social-feed", json={
            "video_id": video_good,
            "platform": "shorts",
        })
        assert res_good.status_code == 200
        data_good = res_good.json()
        assert data_good["vtr"] > 0.7  # strong hook and visual scores yield superior watch threshold VTR

        # Test low hook
        res_bad = client.post("/api/v1/simulation/social-feed", json={
            "video_id": video_bad,
            "platform": "shorts",
        })
        assert res_bad.status_code == 200
        data_bad = res_bad.json()
        assert data_bad["vtr"] < 0.4  # low hook triggers poor VTR

    @pytest.mark.asyncio
    async def test_reels_trend_modifier(self):
        app.dependency_overrides[get_verified_user_id] = lambda: "test-user-1"

        video_id = "reels_vid"
        await store.insert_video(video_id, "reels.mp4", "analyzed")
        await store.insert_analysis(video_id, {
            "hook_score": 75.0,
            "success_probability": 75.0,
            "engagement_curve": [0.75, 0.70, 0.68, 0.65, 0.60],
            "analysis_response": {
                "cortical_response": {
                    "amygdala": 80.0,
                    "visual_cortex": 70.0,
                    "auditory_cortex": 75.0,
                }
            }
        })

        # Run with low sound trend
        res_low = client.post("/api/v1/simulation/social-feed", json={
            "video_id": video_id,
            "platform": "reels",
            "sound_trend_factor": 0.1,
        })
        assert res_low.status_code == 200
        data_low = res_low.json()

        # Run with high sound trend
        res_high = client.post("/api/v1/simulation/social-feed", json={
            "video_id": video_id,
            "platform": "reels",
            "sound_trend_factor": 1.0,
        })
        assert res_high.status_code == 200
        data_high = res_high.json()

        # Verify that changing sound trend scales up VTR, Reels Score and estimated reach
        assert data_high["vtr"] > data_low["vtr"]
        assert data_high["algorithmic_score"] > data_low["algorithmic_score"]
        assert data_high["retention_data"]["reach_multiplier"] > data_low["retention_data"]["reach_multiplier"]

    @pytest.mark.asyncio
    async def test_crud_social_simulations(self):
        app.dependency_overrides[get_verified_user_id] = lambda: "user_abc"

        # Create video & analysis
        video_id = "crud_vid"
        await store.insert_video(video_id, "crud.mp4", "analyzed")
        await store.insert_analysis(video_id, {
            "hook_score": 60.0,
            "success_probability": 60.0,
        })

        # 1. Post a new simulation
        res = client.post("/api/v1/simulation/social-feed", json={
            "video_id": video_id,
            "platform": "shorts",
            "sound_trend_factor": 0.5,
        })
        assert res.status_code == 200
        sim = res.json()
        sim_id = sim["id"]

        # 2. Get the simulation
        res_get = client.get(f"/api/v1/simulation/social-feed/{sim_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == sim_id

        # 3. List simulations for video
        res_history = client.get(f"/api/v1/simulation/social-feed/history/{video_id}")
        assert res_history.status_code == 200
        history = res_history.json()
        assert len(history) == 1
        assert history[0]["id"] == sim_id

        # 4. Delete simulation
        res_del = client.delete(f"/api/v1/simulation/social-feed/{sim_id}")
        assert res_del.status_code == 200

        # Confirm deleted
        res_get_gone = client.get(f"/api/v1/simulation/social-feed/{sim_id}")
        assert res_get_gone.status_code == 404
