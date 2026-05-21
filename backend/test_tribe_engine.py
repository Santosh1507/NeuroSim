"""Tests for TribeEngine — shape validation, determinism, and output structure."""

import pytest
from tribe_engine import TribeEngine


class TestTribeEngineShapeValidation:
    """Verify TribeEngine output structure matches expected schema."""

    @pytest.mark.asyncio
    async def test_simulated_predict_returns_dict(self):
        engine = TribeEngine()
        result = await engine._simulated_predict("test_video.mp4")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_simulated_predict_shape(self):
        engine = TribeEngine()
        result = await engine._simulated_predict("test_video.mp4")
        assert "predictions" in result
        assert "segments" in result
        assert "mode" in result
        assert "is_early_estimate" in result
        assert "confidence_note" in result
        assert result["mode"] == "simulated"
        assert result["is_early_estimate"] is True
        assert result["n_timesteps"] == 20
        assert result["n_vertices"] == 20484

    @pytest.mark.asyncio
    async def test_simulated_predict_predictions_shape(self):
        engine = TribeEngine()
        result = await engine._simulated_predict("test_video.mp4")
        predictions = result["predictions"]
        assert isinstance(predictions, list)
        assert len(predictions) == 20  # n_timesteps
        assert all(len(p) == 20484 for p in predictions)  # n_vertices
        # All values should be between 0 and 1
        for pred in predictions:
            for val in pred:
                assert 0 <= val <= 1

    @pytest.mark.asyncio
    async def test_simulated_predict_segments(self):
        engine = TribeEngine()
        result = await engine._simulated_predict("test_video.mp4")
        segments = result["segments"]
        assert len(segments) == 3
        assert segments[0]["type"] == "hook"
        assert segments[1]["type"] == "body"
        assert segments[2]["type"] == "cta"

    @pytest.mark.asyncio
    async def test_predict_from_text_shape(self):
        engine = TribeEngine()
        result = await engine.predict_from_text("Test script content for analysis")
        assert "predictions" in result
        assert "segments" in result
        assert "mode" in result
        assert result["mode"] == "simulated"
        predictions = result["predictions"]
        assert isinstance(predictions, list)
        assert len(predictions) == 10  # n_timesteps from predict_from_text
        assert all(len(p) == 20484 for p in predictions)

    @pytest.mark.asyncio
    async def test_predict_from_text_empty_string(self):
        engine = TribeEngine()
        result = await engine.predict_from_text("")
        assert "predictions" in result
        assert result["mode"] == "simulated"

    @pytest.mark.asyncio
    async def test_predict_from_video_dispatches_simulated(self):
        """predict_from_video should return simulated when no real model is loaded."""
        engine = TribeEngine()
        assert engine.is_real is False
        result = await engine.predict_from_video("test_video.mp4")
        assert result["mode"] == "simulated"

    @pytest.mark.asyncio
    async def test_same_input_same_output_determinism(self):
        """Same video_path should produce identical predictions."""
        engine = TribeEngine()
        result1 = await engine._simulated_predict("deterministic_test.mp4")
        result2 = await engine._simulated_predict("deterministic_test.mp4")
        assert result1["predictions"] == result2["predictions"]

    @pytest.mark.asyncio
    async def test_different_input_different_output(self):
        """Different video_path should produce different predictions."""
        engine = TribeEngine()
        result1 = await engine._simulated_predict("video_A.mp4")
        result2 = await engine._simulated_predict("video_B.mp4")
        assert result1["predictions"] != result2["predictions"]

    @pytest.mark.asyncio
    async def test_predict_from_text_determinism(self):
        """Same text should produce identical predictions."""
        engine = TribeEngine()
        result1 = await engine.predict_from_text("Hello world this is a test script")
        result2 = await engine.predict_from_text("Hello world this is a test script")
        assert result1["predictions"] == result2["predictions"]

    def test_derive_seed_deterministic(self):
        """_derive_seed should return same value for same input."""
        seed1 = TribeEngine._derive_seed("test content")
        seed2 = TribeEngine._derive_seed("test content")
        assert seed1 == seed2

    def test_derive_seed_different_for_different_content(self):
        """_derive_seed should return different values for different inputs."""
        seed1 = TribeEngine._derive_seed("content A")
        seed2 = TribeEngine._derive_seed("content B")
        assert seed1 != seed2

    def test_derive_seed_returns_int(self):
        """_derive_seed should always return a positive integer."""
        seed = TribeEngine._derive_seed("any content")
        assert isinstance(seed, int)
        assert seed > 0

    def test_derive_seed_empty_string(self):
        """_derive_seed should handle empty strings without error."""
        seed = TribeEngine._derive_seed("")
        assert isinstance(seed, int)


class TestMiroFishDeterminism:
    """Additional determinism tests for MiroFishEngine."""

    @pytest.mark.asyncio
    async def test_mirofish_determinism_same_input(self):
        from mirofish_engine import MiroFishEngine
        engine = MiroFishEngine()
        content = {"transcript": "Hello world test content for determinism check"}
        result1 = await engine.run_simulation(content=content)
        result2 = await engine.run_simulation(content=content)
        assert result1["final_sentiment"] == result2["final_sentiment"]
        assert result1["viral_prediction"] == result2["viral_prediction"]
        assert result1["share_prediction"] == result2["share_prediction"]

    @pytest.mark.asyncio
    async def test_mirofish_different_input_different_output(self):
        from mirofish_engine import MiroFishEngine
        engine = MiroFishEngine()
        r1 = await engine.run_simulation(content={"transcript": "Short video content A"})
        r2 = await engine.run_simulation(content={"transcript": "Much longer video content with different framing and emotional tone"})
        # Extremely unlikely that different content produces same sentiment
        assert r1["final_sentiment"] != r2["final_sentiment"]

    @pytest.mark.asyncio
    async def test_mirofish_determinism_with_roi_scores(self):
        from mirofish_engine import MiroFishEngine
        engine = MiroFishEngine()
        content = {"transcript": "Test content"}
        roi = {"A5": 0.8, "LO": 0.7, "Area45": 0.6, "TPJ": 0.5}
        r1 = await engine.run_simulation(content=content, roi_scores=roi)
        r2 = await engine.run_simulation(content=content, roi_scores=roi)
        assert r1["final_sentiment"] == r2["final_sentiment"]
        assert r1["share_prediction"] == r2["share_prediction"]
