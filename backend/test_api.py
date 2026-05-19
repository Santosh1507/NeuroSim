import io
import os
import random

import numpy as np
import pytest
from fastapi.testclient import TestClient

from config import settings
from storage_adapter import _analyses_cache, _videos_cache
from main import app
from rate_limiter import upload_limiter

# Seed RNGs once at import for module-level determinism.
np.random.seed(42)
random.seed(42)

os.environ["NEUROSIM_SYNC_MODE"] = "1"


def _mp4_header() -> bytes:
    """Return a valid MP4 ftyp header for MIME validation."""
    return bytes.fromhex("000000186674797069736f6d00000001")


@pytest.fixture(autouse=True)
def seed_rng():
    """Re-seed RNGs before each test so results are independent of test order."""
    np.random.seed(42)
    random.seed(42)
    yield


@pytest.fixture(autouse=True)
def clean_dbs():
    _videos_cache.clear()
    _analyses_cache.clear()
    upload_limiter._requests.clear()
    # Ensure upload directory exists (TestClient may not trigger lifespan)
    import os
    os.makedirs(settings.upload_dir, exist_ok=True)
    yield


@pytest.fixture
def client():
    return TestClient(app=app)


class TestAPIEndpoints:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Simulated Analysis" in data["message"]

    def test_models_status(self, client):
        response = client.get("/models/status")
        assert response.status_code == 200
        data = response.json()
        assert "tribev2" in data
        assert "mirofish" in data
        assert data["tribev2"]["status"] == "ready"

    def test_roi_metadata(self, client):
        response = client.get("/roi/metadata")
        assert response.status_code == 200
        data = response.json()
        assert "A5" in data
        assert "LO" in data

    def test_simulate_single_strong(self, client):
        response = client.post("/simulate/single", json={"content_url": "https://example.com/video.mp4", "variant": "a"})
        assert response.status_code == 200
        data = response.json()
        assert "roi" in data
        assert "W_attn" in data
        assert "stage_gate_passed" in data

    def test_simulate_single_weak(self, client):
        response = client.post("/simulate/single", json={"content_url": "https://example.com/video.mp4", "variant": "b"})
        assert response.status_code == 200
        data = response.json()
        assert data["stage_gate_passed"] is False
        assert data["social"] is None

    def test_upload_video(self, client):
        file_content = _mp4_header() + b"fake mp4 content" * 1000
        response = client.post(
            "/upload", files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "video_id" in data

    def test_upload_invalid_content(self, client):
        """Upload with non-video content should be rejected by MIME validation."""
        response = client.post(
            "/upload", files={"file": ("test.mp4", io.BytesIO(b"not a video"), "video/mp4")}
        )
        assert response.status_code == 400

    def test_upload_unsupported_extension(self, client):
        response = client.post(
            "/upload", files={"file": ("test.txt", io.BytesIO(b"not a video"), "text/plain")}
        )
        assert response.status_code == 400

    def test_get_video_not_found(self, client):
        response = client.get("/videos/nonexistent-id")
        assert response.status_code == 404

    def test_get_analysis_not_found(self, client):
        response = client.get("/analyses/nonexistent-id")
        assert response.status_code == 404

    def test_list_videos_empty(self, client):
        response = client.get("/videos")
        assert response.status_code == 200
        data = response.json()
        assert data["videos"] == []

    def _wait_for_analysis(self, client, video_id, max_retries=30):
        for _ in range(max_retries):
            resp = client.get(f"/status/{video_id}")
            if resp.status_code == 200 and resp.json().get("status") == "completed":
                return True
            import time

            time.sleep(0.1)
        return False

    def test_upload_and_retrieve(self, client):
        file_content = _mp4_header() + b"fake mp4 content" * 1000
        upload_response = client.post(
            "/upload", files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        assert upload_response.status_code == 200
        video_id = upload_response.json()["video_id"]
        assert self._wait_for_analysis(client, video_id), "Analysis did not complete"

        video_response = client.get(f"/videos/{video_id}")
        assert video_response.status_code == 200
        assert video_response.json()["video"]["id"] == video_id

        analysis_response = client.get(f"/analyses/{video_id}")
        assert analysis_response.status_code == 200
        analysis = analysis_response.json()
        assert "hook_score" in analysis
        assert "mirofish_simulation" in analysis
        assert "tribev2_brain_response" in analysis
        assert "stage_gate" in analysis

    def test_report_generation(self, client):
        file_content = _mp4_header() + b"fake mp4 content" * 1000
        upload_response = client.post(
            "/upload", files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        video_id = upload_response.json()["video_id"]
        assert self._wait_for_analysis(client, video_id), "Analysis did not complete"

        report_response = client.get(f"/reports/{video_id}")
        assert report_response.status_code == 200
        report = report_response.json()
        assert "report_id" in report
        assert "analysis" in report
        assert "video" in report

    def test_simulation_endpoint(self, client):
        file_content = _mp4_header() + b"fake mp4 content" * 1000
        upload_response = client.post(
            "/upload", files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        video_id = upload_response.json()["video_id"]
        assert self._wait_for_analysis(client, video_id), "Analysis did not complete"

        sim_response = client.get(f"/simulation/{video_id}")
        assert sim_response.status_code == 200
        sim = sim_response.json()
        assert "final_sentiment" in sim
        assert "persona_distribution" in sim

    def test_brain_response_endpoint(self, client):
        file_content = _mp4_header() + b"fake mp4 content" * 1000
        upload_response = client.post(
            "/upload", files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        video_id = upload_response.json()["video_id"]
        assert self._wait_for_analysis(client, video_id), "Analysis did not complete"

        brain_response = client.get(f"/brain-response/{video_id}")
        assert brain_response.status_code == 200
        brain = brain_response.json()
        assert "cortical_response" in brain
        assert "emotional_impact" in brain

    def test_what_if_simulation(self, client):
        file_content = _mp4_header() + b"fake mp4 content" * 1000
        upload_response = client.post(
            "/upload", files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        video_id = upload_response.json()["video_id"]
        assert self._wait_for_analysis(client, video_id), "Analysis did not complete"

        whatif_response = client.post(
            f"/simulation/what-if/{video_id}",
            json={"modifications": {"emotional_tone": True, "price_decrease": 10}},
        )
        assert whatif_response.status_code == 200
        result = whatif_response.json()
        assert "modifications" in result
        assert "predicted_outcome" in result
        assert "comparison" in result

    def test_upload_content_bad_magic_bytes(self, client):
        """Upload with .mp4 extension but garbage content should be rejected."""
        file_content = b"garbage data that doesn't look like a video at all" * 100
        response = client.post(
            "/upload", files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        assert response.status_code == 400
        assert "content" in response.json()["detail"].lower()

    def test_upload_and_delete_analysis(self, client):
        """Upload an analysis, then delete it, then verify it's gone."""
        file_content = _mp4_header() + b"fake mp4 content" * 1000
        upload_response = client.post(
            "/upload", files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        assert upload_response.status_code == 200
        video_id = upload_response.json()["video_id"]
        assert self._wait_for_analysis(client, video_id), "Analysis did not complete"

        # Delete the analysis
        delete_response = client.delete(f"/analyses/{video_id}")
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["status"] == "deleted"
        assert data["video_id"] == video_id

        # Verify it's gone
        get_response = client.get(f"/analyses/{video_id}")
        assert get_response.status_code == 404

        # Delete again should 404
        delete_response2 = client.delete(f"/analyses/{video_id}")
        assert delete_response2.status_code == 404

    def test_pdf_report_download(self, client):
        """PDF report endpoint returns valid PDF bytes."""
        file_content = _mp4_header() + b"fake mp4 content" * 1000
        upload_resp = client.post(
            "/upload", files={"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
        )
        assert upload_resp.status_code == 200
        video_id = upload_resp.json()["video_id"]

        assert self._wait_for_analysis(client, video_id), "Analysis did not complete"

        pdf_resp = client.get(f"/reports/{video_id}/pdf")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert pdf_resp.content[:4] == b"%PDF"
