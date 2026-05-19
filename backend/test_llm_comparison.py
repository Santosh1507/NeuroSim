"""Tests for LLM scorer vs heuristic comparison."""
import pytest


class TestLLMScorer:
    def test_disabled_without_api_key(self):
        from llm_scorer import LLMScorer
        scorer = LLMScorer(api_key=None, use_env=False)
        result = scorer.score_transcript("test")
        assert result["mode"] == "disabled"
        assert "error" in result

    def test_disabled_with_empty_key(self):
        from llm_scorer import LLMScorer
        scorer = LLMScorer(api_key="", use_env=False)
        result = scorer.score_transcript("test")
        assert result["mode"] == "disabled"

    def test_enabled_with_api_key(self):
        from llm_scorer import LLMScorer
        scorer = LLMScorer(api_key="sk-fake-key")
        assert scorer.enabled is True

    def test_same_format_as_heuristic(self):
        from heuristic_scorer import score_transcript
        from llm_scorer import LLMScorer
        heuristic = score_transcript("Hello world, this is a test video.")
        assert all(k in heuristic for k in ["A5", "LO", "Area45", "TPJ"])

    def test_heuristic_returns_valid_scores(self):
        from heuristic_scorer import score_transcript
        transcript = "Hello world, this is a test video with some content."
        result = score_transcript(transcript)
        assert isinstance(result["A5"], (int, float))
        assert isinstance(result["LO"], (int, float))
        assert isinstance(result["Area45"], (int, float))
        assert isinstance(result["TPJ"], (int, float))

    def test_heuristic_scores_in_range(self):
        from heuristic_scorer import score_transcript
        transcript = "Buy now! Click the link below and subscribe to my channel."
        result = score_transcript(transcript)
        for key in ["A5", "LO", "Area45", "TPJ"]:
            assert 0 <= result[key] <= 100
