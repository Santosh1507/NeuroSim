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


_SAMPLE_SCRIPT = """
Have you ever wondered why some videos go viral while others flop?
Today I'm going to show you the three secrets that top creators use
to hook viewers in the first three seconds. Stick around because
number three will completely change how you think about content.
First, you need a pattern interrupt. Something that breaks the
viewer's scrolling habit instantly. Second, create a curiosity gap
that makes them need to know the answer. And third, deliver on
your promise with a payoff that makes them want to share it with
their friends. If you found this helpful, hit subscribe and let
me know in the comments which tip you're going to try first.
""".strip()


class TestScriptAnalysis:
    def test_analyze_script_success(self, client):
        """Script analysis returns full analysis structure instantly."""
        response = client.post("/api/analyze/script", json={"script": _SAMPLE_SCRIPT})
        assert response.status_code == 200
        data = response.json()
        assert "hook_score" in data
        assert "viral_potential" in data
        assert "success_probability" in data
        assert "risk_score" in data
        assert "recommendations" in data
        assert "tribev2_brain_response" in data
        assert "mirofish_simulation" in data
        assert "stage_gate" in data
        assert data["analysis_type"] == "script"
        assert data["source"] == "text_input"
        assert data["video_id"].startswith("script_")

    def test_analyze_script_roi_scores(self, client):
        """Script analysis returns valid ROI scores in 0-1 range."""
        response = client.post("/api/analyze/script", json={"script": _SAMPLE_SCRIPT})
        brain = response.json()["tribev2_brain_response"]["cortical_response"]
        assert 0 <= brain["auditory_cortex"] <= 100
        assert 0 <= brain["visual_cortex"] <= 100
        assert 0 <= brain["language_center"] <= 100
        assert 0 <= brain["amygdala"] <= 100
        assert 0 <= brain["prefrontal_cortex"] <= 100
        assert 0 <= brain["reward_center"] <= 100

    def test_analyze_script_with_title(self, client):
        """Script analysis accepts optional title field."""
        response = client.post(
            "/api/analyze/script",
            json={"script": _SAMPLE_SCRIPT, "title": "My Viral Video Script"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["script_title"] == "My Viral Video Script"

    def test_analyze_script_empty_rejected(self, client):
        """Empty script text returns 400."""
        response = client.post("/api/analyze/script", json={"script": ""})
        assert response.status_code == 400

    def test_analyze_script_whitespace_only_rejected(self, client):
        """Whitespace-only script returns 400."""
        response = client.post("/api/analyze/script", json={"script": "   \n\n  "})
        assert response.status_code == 400

    def test_analyze_script_too_short_rejected(self, client):
        """Script under 50 characters returns 400."""
        response = client.post("/api/analyze/script", json={"script": "Too short!"})
        assert response.status_code == 400

    def test_analyze_script_stored_in_cache(self, client):
        """Script analysis is stored in the analysis cache."""
        response = client.post("/api/analyze/script", json={"script": _SAMPLE_SCRIPT})
        video_id = response.json()["video_id"]

        fetch = client.get(f"/analyses/{video_id}")
        assert fetch.status_code == 200
        assert fetch.json()["video_id"] == video_id

    def test_analyze_script_listed_in_videos(self, client):
        """Script analysis appears in video listing."""
        response = client.post(
            "/api/analyze/script",
            json={"script": _SAMPLE_SCRIPT, "title": "Test Script"},
        )
        video_id = response.json()["video_id"]

        videos_resp = client.get("/videos")
        assert videos_resp.status_code == 200
        video_ids = [v["id"] for v in videos_resp.json()["videos"]]
        assert video_id in video_ids
