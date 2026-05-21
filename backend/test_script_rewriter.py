import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from main import app
from storage_adapter import _analyses_cache, _videos_cache
from config import settings

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def clean_caches():
    _videos_cache.clear()
    _analyses_cache.clear()
    yield

def test_rewrite_script_raw_input_mock_fallback(client):
    # Test the fallback simulation when GEMINI_API_KEY is not set
    with patch("config.settings.gemini_api_key", None), patch.dict("os.environ", {}, clear=False):
        payload = {
            "script": "Hello world! This is a test script for NeuroSim, a platform for neural simulation.",
            "dimension": "hook",
            "additional_instructions": "Make it sound exciting!"
        }
        response = client.post("/api/v1/analyze/rewrite", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "rewritten_script" in data
        assert "explanation" in data
        assert "estimated_improvements" in data
        assert data["estimated_improvements"]["before_score"] == 50
        assert data["estimated_improvements"]["after_score"] == 90

def test_rewrite_script_video_id_mock_fallback(client):
    # Seed analysis in cache
    video_id = "test_video_123"
    _analyses_cache[video_id] = {
        "full_transcript": "We are building amazing systems and this is the original transcript.",
        "transcript": "We are building amazing systems and this is the original transcript."
    }
    
    with patch("config.settings.gemini_api_key", None), patch.dict("os.environ", {}, clear=False):
        payload = {
            "video_id": video_id,
            "dimension": "cta"
        }
        response = client.post("/api/v1/analyze/rewrite", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "rewritten_script" in data
        assert "estimated_improvements" in data
        assert data["estimated_improvements"]["after_score"] == 85

def test_rewrite_script_invalid_dimension(client):
    payload = {
        "script": "Some script long enough to satisfy.",
        "dimension": "invalid_dimension"
    }
    response = client.post("/api/v1/analyze/rewrite", json=payload)
    assert response.status_code == 400
    assert "Invalid dimension" in response.json()["detail"]

def test_rewrite_script_missing_content(client):
    payload = {
        "dimension": "hook"
    }
    response = client.post("/api/v1/analyze/rewrite", json=payload)
    assert response.status_code == 400
    assert "No script content found or provided." in response.json()["detail"]

def test_rewrite_script_gemini_client_success(client):
    # Test when API key is set and genai.Client is called
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"rewritten_script": "Synthesized boosted hook text", "explanation": "Boosted using Gemini", "estimated_improvements": {"before_score": 40, "after_score": 95, "rationale": "High quality hook"}}'
    mock_client.models.generate_content.return_value = mock_response

    mock_genai = MagicMock()
    mock_genai.Client.return_value = mock_client

    # Patch google.genai at routes.analysis level and settings/os.environ
    with patch("routes.analysis.genai", mock_genai), \
         patch("routes.analysis._GENAI_AVAILABLE", True), \
         patch("routes.analysis.genai_types", MagicMock()), \
         patch("config.settings.gemini_api_key", "fake-api-key"):
        payload = {
            "script": "Hello world! This is a test script for NeuroSim, a platform for neural simulation.",
            "dimension": "hook"
        }
        response = client.post("/api/v1/analyze/rewrite", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["rewritten_script"] == "Synthesized boosted hook text"
        assert data["explanation"] == "Boosted using Gemini"
        assert data["estimated_improvements"]["after_score"] == 95

