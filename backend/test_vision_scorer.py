"""Tests for vision_scorer module."""

import os
import pytest
from unittest.mock import patch, MagicMock

from vision_scorer import VisionScorer


class TestVisionScorerInit:
    def test_disabled_without_api_key(self):
        scorer = VisionScorer(api_key="")
        assert not scorer.enabled

    def test_enabled_with_api_key(self):
        scorer = VisionScorer(api_key="test-key")
        assert scorer.enabled

    def test_reads_from_env(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "env-key"}):
            scorer = VisionScorer()
            assert scorer.enabled

    def test_default_model(self):
        scorer = VisionScorer(api_key="test")
        assert scorer.model == "gemini-2.5-flash"

    def test_custom_model(self):
        scorer = VisionScorer(api_key="test", model="gemini-2.0-flash")
        assert scorer.model == "gemini-2.0-flash"


class TestVisionScorerExtractJson:
    def setup_method(self):
        self.scorer = VisionScorer(api_key="test")

    def test_plain_json(self):
        text = '{"hook_score": 0.7, "hold_rate": 0.6}'
        result = self.scorer._extract_json(text)
        assert result["hook_score"] == 0.7

    def test_markdown_wrapped(self):
        text = '```json\n{"hook_score": 0.8}\n```'
        result = self.scorer._extract_json(text)
        assert result["hook_score"] == 0.8

    def test_no_json_raises_error(self):
        with pytest.raises(ValueError):
            self.scorer._extract_json("no json here")


class TestVisionScorerValidate:
    def setup_method(self):
        self.scorer = VisionScorer(api_key="test")

    def test_valid_response(self):
        data = {
            "hook_score": 0.7, "hold_rate": 0.6, "virality_score": 65,
            "engagement_curve": [0.8, 0.6], "visual_engagement": 0.7,
            "audio_engagement": 0.6, "emotional_arc": 0.5,
            "cta_presence": 0.3, "peak_hook_timestamp": 1.0,
            "brain_regions": {"visual_cortex": 0.8},
            "recommendations": ["test"],
        }
        assert self.scorer._validate_response(data)

    def test_missing_field(self):
        data = {"hook_score": 0.7}
        assert not self.scorer._validate_response(data)

    def test_wrong_type(self):
        data = {
            "hook_score": "not_a_number", "hold_rate": 0.6, "virality_score": 65,
            "engagement_curve": [0.8], "visual_engagement": 0.7,
            "audio_engagement": 0.6, "emotional_arc": 0.5,
            "cta_presence": 0.3, "peak_hook_timestamp": 1.0,
            "brain_regions": {}, "recommendations": [],
        }
        assert not self.scorer._validate_response(data)


class TestVisionScorerClamp:
    def setup_method(self):
        self.scorer = VisionScorer(api_key="test")

    def test_clamp_within_range(self):
        assert self.scorer._clamp(0.5) == 0.5

    def test_clamp_above_max(self):
        assert self.scorer._clamp(1.5) == 1.0

    def test_clamp_below_min(self):
        assert self.scorer._clamp(-0.3) == 0.0

    def test_clamp_custom_range(self):
        assert self.scorer._clamp(150, 0, 100) == 100


class TestVisionScorerFallback:
    def test_fallback_returns_varied_scores(self):
        scorer = VisionScorer(api_key="")
        result = scorer.get_fallback_scores(duration_seconds=5, seed=42)
        assert result["mode"] == "fallback"
        # Scores should be in the realistic 0.30-0.70 range, not flat 0.5
        assert 0.30 <= result["hook_score"] <= 0.70
        assert len(result["engagement_curve"]) == 5
        # Each curve point should also be in the varied range
        assert all(0.30 <= v <= 0.75 for v in result["engagement_curve"])

    def test_fallback_deterministic_with_seed(self):
        scorer = VisionScorer(api_key="")
        result1 = scorer.get_fallback_scores(seed=42)
        result2 = scorer.get_fallback_scores(seed=42)
        assert result1["hook_score"] == result2["hook_score"]
        assert result1["virality_score"] == result2["virality_score"]
        assert result1["engagement_curve"] == result2["engagement_curve"]

    def test_fallback_different_seeds_different_scores(self):
        scorer = VisionScorer(api_key="")
        result1 = scorer.get_fallback_scores(seed=42)
        result2 = scorer.get_fallback_scores(seed=99)
        # Different seed should produce different scores
        assert result1["hook_score"] != result2["hook_score"]

    def test_fallback_has_all_fields(self):
        scorer = VisionScorer(api_key="")
        result = scorer.get_fallback_scores()
        required = ["hook_score", "hold_rate", "virality_score", "engagement_curve",
                     "visual_engagement", "audio_engagement", "emotional_arc",
                     "cta_presence", "peak_hook_timestamp", "brain_regions",
                     "recommendations", "mode"]
        for field in required:
            assert field in result

    def test_fallback_brain_regions_count(self):
        scorer = VisionScorer(api_key="")
        result = scorer.get_fallback_scores()
        assert len(result["brain_regions"]) == 6

    def test_fallback_string_seed(self):
        scorer = VisionScorer(api_key="")
        # String seeds should be hashed to deterministic int
        result1 = scorer.get_fallback_scores(seed="my_video.mp4")
        result2 = scorer.get_fallback_scores(seed="my_video.mp4")
        assert result1["hook_score"] == result2["hook_score"]

    def test_fallback_different_strings_different_scores(self):
        scorer = VisionScorer(api_key="")
        result1 = scorer.get_fallback_scores(seed="video_a.mp4")
        result2 = scorer.get_fallback_scores(seed="video_b.mp4")
        assert result1["hook_score"] != result2["hook_score"]


class TestVisionScorerDisabled:
    def test_analyze_returns_disabled(self):
        scorer = VisionScorer(api_key="")
        result = scorer.analyze_video("/tmp/test.mp4")
        assert result["mode"] == "disabled"
        assert "error" in result


class TestVisionScorerAnalyze:
    @patch("vision_scorer.logger")
    def test_analyze_video_success(self, mock_logger):
        scorer = VisionScorer(api_key="mock-key")
        mock_client = MagicMock()
        scorer._client = mock_client

        mock_file = MagicMock()
        mock_file.name = "files/test-file"
        mock_file.state.name = "ACTIVE"
        mock_client.files.upload.return_value = mock_file

        mock_response = MagicMock()
        mock_response.text = '{"hook_score": 0.8, "hold_rate": 0.7, "virality_score": 75, "engagement_curve": [0.8, 0.7], "visual_engagement": 0.8, "audio_engagement": 0.7, "emotional_arc": 0.6, "cta_presence": 0.4, "peak_hook_timestamp": 0, "brain_regions": {"visual_cortex": 0.8, "auditory_cortex": 0.7, "amygdala": 0.6, "prefrontal": 0.5, "memory": 0.6, "social_cognition": 0.6}, "recommendations": ["Optimize the intro"]}'
        mock_client.models.generate_content.return_value = mock_response

        result = scorer.analyze_video("dummy_path.mp4")

        assert result["mode"] == "vision"
        assert result["hook_score"] == 0.8
        assert result["hold_rate"] == 0.7
        assert result["virality_score"] == 75.0

        mock_client.files.upload.assert_called_once_with(file="dummy_path.mp4")
        mock_client.files.delete.assert_called_once_with(name="files/test-file")

    @patch("vision_scorer.logger")
    def test_analyze_video_with_polling(self, mock_logger):
        scorer = VisionScorer(api_key="mock-key")
        mock_client = MagicMock()
        scorer._client = mock_client

        mock_file_processing = MagicMock()
        mock_file_processing.name = "files/test-file"
        mock_file_processing.state.name = "PROCESSING"

        mock_file_active = MagicMock()
        mock_file_active.name = "files/test-file"
        mock_file_active.state.name = "ACTIVE"

        mock_client.files.upload.return_value = mock_file_processing
        mock_client.files.get.return_value = mock_file_active

        mock_response = MagicMock()
        mock_response.text = '{"hook_score": 0.8, "hold_rate": 0.7, "virality_score": 75, "engagement_curve": [0.8, 0.7], "visual_engagement": 0.8, "audio_engagement": 0.7, "emotional_arc": 0.6, "cta_presence": 0.4, "peak_hook_timestamp": 0, "brain_regions": {"visual_cortex": 0.8, "auditory_cortex": 0.7, "amygdala": 0.6, "prefrontal": 0.5, "memory": 0.6, "social_cognition": 0.6}, "recommendations": []}'
        mock_client.models.generate_content.return_value = mock_response

        result = scorer.analyze_video("dummy_path.mp4")

        assert result["mode"] == "vision"
        mock_client.files.get.assert_called_once_with(name="files/test-file")
        mock_client.files.delete.assert_called_once_with(name="files/test-file")

