"""Tests for LLM scorer and heuristic comparison."""

import pytest
from llm_scorer import LLMScorer
from heuristic_scorer import score_transcript as heuristic_score


class TestLLMScorer:
    def test_disabled_without_api_key(self):
        scorer = LLMScorer(api_key=None)
        result = scorer.score_transcript("test")
        assert result["mode"] == "disabled"

    def test_disabled_with_empty_api_key(self):
        scorer = LLMScorer(api_key="")
        assert scorer.enabled is False

    def test_score_transcript_returns_required_keys(self):
        scorer = LLMScorer(api_key=None)
        result = scorer.score_transcript("Hello world")
        for key in ["A5", "LO", "Area45", "TPJ"]:
            assert key in result, f"Missing key: {key}"
        assert "mode" in result
        assert "word_count" in result

    def test_scores_are_floats(self):
        scorer = LLMScorer(api_key=None)
        result = scorer.score_transcript("Hello world, this is a test video script.")
        for key in ["A5", "LO", "Area45", "TPJ"]:
            assert isinstance(result[key], float), f"{key} should be float"

    def test_scores_in_range(self):
        scorer = LLMScorer(api_key=None)
        result = scorer.score_transcript("Hello world, this is a test video script.")
        for key in ["A5", "LO", "Area45", "TPJ"]:
            assert 0.0 <= result[key] <= 1.0, f"{key} out of range: {result[key]}"

    def test_empty_transcript(self):
        scorer = LLMScorer(api_key=None)
        result = scorer.score_transcript("")
        assert result["mode"] == "disabled"
        assert result["word_count"] == 0

    def test_same_format_as_heuristic(self):
        text = "Hello world, this is a test video script."
        heuristic = heuristic_score(text)
        scorer = LLMScorer(api_key=None)
        llm_result = scorer.score_transcript(text)
        for key in ["A5", "LO", "Area45", "TPJ", "mode", "word_count"]:
            assert key in llm_result, f"LLM result missing key: {key}"
            assert key in heuristic, f"Heuristic result missing key: {key}"
        assert heuristic["mode"] == "heuristic"
        assert llm_result["mode"] in ("disabled", "llm", "error")


class TestHeuristicLLMShapeParity:
    """Verify that heuristic and LLM scorers produce structurally identical output."""

    TEST_CASES = [
        "Simple short script.",
        "This is a longer video script that goes into more detail about the topic. It has multiple sentences and covers several points.",
        "Hey guys! Welcome back to the channel. Today we're going to talk about something that's going to blow your mind. Make sure you stick around until the end because I've got a special surprise for you. Don't forget to like and subscribe!",
    ]

    def test_heuristic_shape(self):
        for text in self.TEST_CASES:
            result = heuristic_score(text)
            assert set(result.keys()) >= {"A5", "LO", "Area45", "TPJ", "mode", "word_count"}
            for key in ["A5", "LO", "Area45", "TPJ"]:
                assert isinstance(result[key], float)
                assert 0.0 <= result[key] <= 1.0

    def test_llm_disabled_shape(self):
        scorer = LLMScorer(api_key=None)
        for text in self.TEST_CASES:
            result = scorer.score_transcript(text)
            assert set(result.keys()) >= {"A5", "LO", "Area45", "TPJ", "mode", "word_count"}
            for key in ["A5", "LO", "Area45", "TPJ"]:
                assert isinstance(result[key], float)
                assert 0.0 <= result[key] <= 1.0

    def test_heuristic_determinism(self):
        text = "This is a test script for determinism checking."
        r1 = heuristic_score(text)
        r2 = heuristic_score(text)
        for key in ["A5", "LO", "Area45", "TPJ"]:
            assert r1[key] == r2[key], f"Heuristic {key} not deterministic"
