"""Tests for the Virality Predictor endpoint."""

import io
import os
from unittest.mock import PropertyMock, patch

import pytest
from fastapi.testclient import TestClient

from config import settings
from main import app
from rate_limiter import predict_limiter
from vision_scorer import vision_scorer

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_state():
    predict_limiter._requests.clear()
    os.makedirs(settings.upload_dir, exist_ok=True)

    with patch("transcriber.Transcriber.available", new_callable=PropertyMock) as mock_avail, \
         patch("transcriber.Transcriber.transcribe") as mock_trans:
        mock_avail.return_value = True
        mock_trans.return_value = "This is a beautiful test video, please click subscribe and download now!"
        yield

    predict_limiter._requests.clear()


def _mp4_header() -> bytes:
    """Return a valid MP4 ftyp header for MIME validation."""
    return bytes.fromhex("000000186674797069736f6d00000001")


def _make_video() -> io.BytesIO:
    """Small valid-ish video for test requests."""
    return io.BytesIO(_mp4_header() + b"fake video content" * 500)


class TestPredictEndpoint:
    def test_predict_video_success(self):
        """Predict endpoint returns virality scores for a valid video."""
        response = client.post(
            "/api/v1/predict",
            files={"file": ("test_clip.mp4", _make_video(), "video/mp4")},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("hook_score"), (int, float))
        assert isinstance(data.get("authenticity_score"), (int, float))
        assert isinstance(data.get("viral_potential"), (int, float))
        assert isinstance(data.get("success_probability"), (int, float))
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0
        assert "video_id" in data
        assert "stage_gate" in data

    def test_predict_returns_all_required_fields(self):
        """Predict response includes all documented fields."""
        response = client.post(
            "/api/v1/predict",
            files={"file": ("clip.mp4", _make_video(), "video/mp4")},
        )
        assert response.status_code == 200
        data = response.json()

        assert "video_id" in data
        assert "analysis_mode" in data
        assert "hook_score" in data
        assert "hook_strength" in data
        assert "authenticity_score" in data
        assert "viral_potential" in data
        assert "success_probability" in data

        assert "roi_scores" in data
        for region in ("A5", "LO", "Area45", "TPJ"):
            assert region in data["roi_scores"]

        assert "stage_gate" in data
        assert "passed" in data["stage_gate"]
        assert "W_attn" in data["stage_gate"]

        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) <= 8
        assert "created_at" in data

    def test_predict_invalid_extension_rejected(self):
        """Non-video file extensions are rejected."""
        response = client.post(
            "/api/v1/predict",
            files={"file": ("script.txt", io.BytesIO(b"not a video"), "text/plain")},
        )
        assert response.status_code == 400
        assert "Unsupported format" in response.json()["detail"]

    def test_predict_bad_magic_bytes_rejected(self):
        """File with .mp4 extension but garbage content is rejected."""
        response = client.post(
            "/api/v1/predict",
            files={"file": ("clip.mp4", io.BytesIO(b"garbage content" * 100), "video/mp4")},
        )
        assert response.status_code == 400
        assert "not match" in response.json()["detail"].lower()

    def test_predict_large_file_rejected(self):
        """Files over 100MB are rejected with 400."""
        content = _mp4_header() + b"x" * 105 * 1024 * 1024  # 105MB
        response = client.post(
            "/api/v1/predict",
            files={"file": ("large.mp4", io.BytesIO(content), "video/mp4")},
        )
        assert response.status_code == 400

    def test_predict_rate_limited(self):
        """Predict endpoint rate limits after 10 requests per minute per IP."""
        video = _make_video()

        # Send 10 requests that should all be allowed
        for i in range(10):
            video.seek(0)
            response = client.post(
                "/api/v1/predict",
                files={"file": ("clip.mp4", video, "video/mp4")},
            )
            # Some may error on Gemini/no-ffprobe but should NOT be 429
            assert response.status_code != 429, f"Request {i+1} was rate limited too early"

        # The 11th should be rate limited
        video.seek(0)
        response = client.post(
            "/api/v1/predict",
            files={"file": ("clip.mp4", video, "video/mp4")},
        )
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()

    def test_predict_with_vision_scores(self):
        """Predict endpoint includes vision scores when Gemini returns them."""
        original = vision_scorer.analyze_video

        def mock_analyze(path):
            return {
                "mode": "vision",
                "hook_score": 0.8,
                "hold_rate": 0.7,
                "virality_score": 75,
                "engagement_curve": [0.8, 0.7, 0.6, 0.5],
                "visual_engagement": 0.8,
                "audio_engagement": 0.7,
                "emotional_arc": 0.6,
                "cta_presence": 0.4,
                "peak_hook_timestamp": 0.5,
                "brain_regions": {
                    "visual_cortex": 0.8, "auditory_cortex": 0.7,
                    "amygdala": 0.6, "prefrontal": 0.5,
                    "memory": 0.6, "social_cognition": 0.5,
                },
                "recommendations": ["Add a human face in first frame"],
            }

        vision_scorer.analyze_video = mock_analyze
        try:
            response = client.post(
                "/api/v1/predict",
                files={"file": ("clip.mp4", _make_video(), "video/mp4")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["analysis_mode"] == "vision+heuristic"
            assert data["virality_score"] == 75
            assert data["hold_rate"] == 70.0
            assert data["brain_regions"] is not None
        finally:
            vision_scorer.analyze_video = original

    def test_predict_uses_fallback_when_vision_disabled(self):
        """Predict endpoint returns non-null fallback video scores without Gemini."""
        original = vision_scorer.analyze_video

        def mock_disabled(path):
            return {"mode": "disabled", "error": "Vision scoring not configured"}

        vision_scorer.analyze_video = mock_disabled
        try:
            response = client.post(
                "/api/v1/predict",
                files={"file": ("clip.mp4", _make_video(), "video/mp4")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["analysis_mode"] == "fallback+heuristic"
            assert data["virality_score"] is not None
            assert data["hold_rate"] is not None
            assert data["engagement_curve"]
            assert data["brain_regions"] is not None
        finally:
            vision_scorer.analyze_video = original
