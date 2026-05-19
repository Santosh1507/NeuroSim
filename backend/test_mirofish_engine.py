"""Tests for MiroFishEngine — simulated mode."""

import os
import random

import numpy as np
import pytest

from mirofish_engine import MiroFishEngine


# Use sync-mode sleep durations so tests don't wait 0.8s per call
os.environ["NEUROSIM_SYNC_MODE"] = "1"

np.random.seed(42)
random.seed(42)


@pytest.fixture(autouse=True)
def seed_rng():
    np.random.seed(42)
    random.seed(42)
    yield


@pytest.fixture
def engine():
    eng = MiroFishEngine()
    eng.is_real = False  # force simulated mode
    return eng


class TestMiroFishEngine:
    """Tests for the simulated MiroFish swarm simulation."""

    @pytest.mark.asyncio
    async def test_simulated_simulation_returns_expected_structure(self, engine):
        result = await engine.run_simulation(content={"transcript": "Test video content"})
        assert isinstance(result, dict)
        assert "simulation_id" in result
        assert "mode" in result
        assert result["mode"] == "simulated"
        assert "persona_distribution" in result
        assert "final_sentiment" in result
        assert "viral_prediction" in result
        assert "backlash_prediction" in result
        assert "share_prediction" in result
        assert "trust_trajectory" in result
        assert "comment_samples" in result
        assert "simulation_rounds" in result
        assert "num_agents" in result

    @pytest.mark.asyncio
    async def test_simulated_simulation_default_params(self, engine):
        result = await engine.run_simulation(content={"transcript": "Hello world"})
        assert result["num_agents"] == 1000
        assert result["simulation_rounds"] == 20
        assert 0 <= result["final_sentiment"] <= 100

    @pytest.mark.asyncio
    async def test_simulated_simulation_custom_params(self, engine):
        result = await engine.run_simulation(
            content={"transcript": "Test"},
            num_agents=100,
            simulation_rounds=5,
        )
        assert result["num_agents"] == 100
        assert result["simulation_rounds"] == 5

    @pytest.mark.asyncio
    async def test_simulated_simulation_with_roi_scores(self, engine):
        result = await engine.run_simulation(
            content={"transcript": "Great content"},
            roi_scores={"A5": 0.8, "LO": 0.9, "Area45": 0.7, "TPJ": 0.6},
        )
        # ROI boost should push sentiment higher
        assert result["final_sentiment"] > 0
        assert result["share_prediction"] > 0

    @pytest.mark.asyncio
    async def test_comment_samples_contains_three_types(self, engine):
        result = await engine.run_simulation(content={"transcript": "Test content"})
        samples = result["comment_samples"]
        assert len(samples) > 0
        types_found = {s["type"] for s in samples}
        # Should have at least one of positive/negative/neutral
        assert types_found.intersection({"positive", "negative", "neutral"})

    @pytest.mark.asyncio
    async def test_persona_distribution_sums_to_100(self, engine):
        result = await engine.run_simulation(content={"transcript": "Test"})
        total = sum(result["persona_distribution"].values())
        assert abs(total - 100.0) < 0.5  # allow rounding

    @pytest.mark.asyncio
    async def test_trust_trajectory_length_matches_rounds(self, engine):
        result = await engine.run_simulation(
            content={"transcript": "Test"},
            simulation_rounds=5,
        )
        assert len(result["trust_trajectory"]) == 5

    @pytest.mark.asyncio
    async def test_viral_prediction_is_reasonable_string(self, engine):
        result = await engine.run_simulation(content={"transcript": "Test"})
        valid = {"High", "Moderate", "Low", "At Risk"}
        prefix = result["viral_prediction"].split(" - ")[0]
        assert prefix in valid, f"Unexpected viral prediction: {result['viral_prediction']}"

    @pytest.mark.asyncio
    async def test_backlash_prediction_is_reasonable_string(self, engine):
        result = await engine.run_simulation(content={"transcript": "Test"})
        assert "risk" in result["backlash_prediction"].lower()

    @pytest.mark.asyncio
    async def test_simulated_simulation_empty_content(self, engine):
        """Should handle empty or minimal content gracefully."""
        result = await engine.run_simulation(content={"transcript": ""})
        assert isinstance(result["final_sentiment"], (int, float))


class TestWhatIfSimulation:
    """Tests for the what-if simulation feature."""

    @pytest.mark.asyncio
    async def test_what_if_returns_expected_structure(self, engine):
        base_sim = await engine.run_simulation(content={"transcript": "Base content"})
        result = await engine.run_what_if(base_sim, {"emotional_tone": True})
        assert "modifications" in result
        assert "predicted_outcome" in result
        assert "comparison" in result

    @pytest.mark.asyncio
    async def test_what_if_modifications_empty(self, engine):
        base_sim = await engine.run_simulation(content={"transcript": "Base"})
        result = await engine.run_what_if(base_sim, {})
        assert result["modifications"] == []
        assert result["predicted_outcome"]["sentiment_adjustment"] == 0

    @pytest.mark.asyncio
    async def test_what_if_emotional_tone(self, engine):
        base_sim = await engine.run_simulation(content={"transcript": "Base"})
        result = await engine.run_what_if(base_sim, {"emotional_tone": True})
        mods = result["modifications"]
        assert any(m["effect"] == "positive" for m in mods)

    @pytest.mark.asyncio
    async def test_what_if_earlier_product_mention(self, engine):
        base_sim = await engine.run_simulation(content={"transcript": "Base"})
        result = await engine.run_what_if(base_sim, {"earlier_product_mention": True})
        mods = result["modifications"]
        assert any(m["effect"] == "negative" for m in mods)

    @pytest.mark.asyncio
    async def test_what_if_price_decrease(self, engine):
        base_sim = await engine.run_simulation(content={"transcript": "Base"})
        result = await engine.run_what_if(base_sim, {"price_decrease": 20})
        mods = result["modifications"]
        pos = [m for m in mods if m["effect"] == "positive"]
        assert len(pos) > 0
        assert pos[0]["magnitude"] == 0.06  # 20/100 * 0.3

    @pytest.mark.asyncio
    async def test_what_if_aggressive_cta(self, engine):
        base_sim = await engine.run_simulation(content={"transcript": "Base"})
        result = await engine.run_what_if(base_sim, {"aggressive_cta": True})
        mods = result["modifications"]
        assert any(m["effect"] == "negative" for m in mods)

    @pytest.mark.asyncio
    async def test_what_if_multiple_modifications(self, engine):
        base_sim = await engine.run_simulation(content={"transcript": "Base"})
        result = await engine.run_what_if(
            base_sim,
            {
                "emotional_tone": True,
                "price_decrease": 10,
                "aggressive_cta": True,
            },
        )
        mods = result["modifications"]
        assert len(mods) == 3
        positive = sum(m["magnitude"] for m in mods if m["effect"] == "positive")
        negative = sum(m["magnitude"] for m in mods if m["effect"] == "negative")
        net = round(positive - negative, 3)
        assert result["predicted_outcome"]["sentiment_adjustment"] == net

    @pytest.mark.asyncio
    async def test_what_if_comparison_structure(self, engine):
        base_sim = await engine.run_simulation(content={"transcript": "Base"})
        result = await engine.run_what_if(base_sim, {"emotional_tone": True})
        comp = result["comparison"]
        assert "original_sentiment" in comp
        assert "modified_sentiment" in comp
        assert isinstance(comp["original_sentiment"], (int, float))
        assert isinstance(comp["modified_sentiment"], (int, float))

    @pytest.mark.asyncio
    async def test_what_if_real_mode_fallback(self, engine):
        """When is_real=True but API is down, should fall back to simulated."""
        engine.is_real = True
        engine.api_url = "http://localhost:1"  # will fail quickly
        base_sim = await engine.run_simulation(content={"transcript": "Base"})
        result = await engine.run_what_if(base_sim, {"emotional_tone": True})
        # Should still return simulated result (fallback)
        assert "modifications" in result
