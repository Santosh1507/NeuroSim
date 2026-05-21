"""Tests for heuristic_scorer module."""

from heuristic_scorer import score_transcript


class TestHeuristicScorer:
    def test_empty_transcript(self):
        result = score_transcript("")
        # Empty transcript now returns varied fallback scores (not flat 0.5)
        for key in ("A5", "LO", "Area45", "TPJ"):
            assert 0.0 <= result[key] <= 1.0, f"{key} out of range: {result[key]}"
        assert result["mode"] == "fallback"
        assert result["word_count"] == 0
        assert "empty transcript" in result.get("note", "")

    def test_all_scores_in_range(self):
        text = "This is a test transcript with some content to analyze."
        result = score_transcript(text)
        for key in ("A5", "LO", "Area45", "TPJ"):
            assert 0.0 <= result[key] <= 1.0, f"{key} out of range: {result[key]}"

    def test_cta_heavy_text(self):
        text = "Click now to subscribe and buy our amazing product! Get started today with this exclusive limited offer. Don't miss out — act now and download your free trial!"
        result = score_transcript(text)
        assert result["Area45"] > 0.5, f"CTA text should have high Area45, got {result['Area45']}"

    def test_question_heavy_text(self):
        text = "What if you could change everything? Why do we accept the status quo? How can we build a better community together? Who will lead the way? When will we act?"
        result = score_transcript(text)
        assert result["TPJ"] > 0.4, f"Question text should have high TPJ, got {result['TPJ']}"

    def test_visual_heavy_text(self):
        text = "Look at this beautiful scene. The bright colors shine through the clear landscape. You can see the stunning visual display of vivid imagery. Watch the glow appear in the dark sky."
        result = score_transcript(text)
        assert result["LO"] > 0.3, f"Visual text should have elevated LO, got {result['LO']}"

    def test_social_heavy_text(self):
        text = "We are a community of friends and family who work together. Our team shares everything with everyone. Together we build a society that collaborates and supports each other."
        result = score_transcript(text)
        assert result["TPJ"] > 0.3, f"Social text should have elevated TPJ, got {result['TPJ']}"

    def test_mode_is_heuristic(self):
        result = score_transcript("Hello world")
        assert result["mode"] == "heuristic"

    def test_word_count(self):
        text = "one two three four five"
        result = score_transcript(text)
        assert result["word_count"] == 5

    def test_mixed_content(self):
        text = (
            "Look at this amazing product! What makes it special? "
            "We built it together for our community. "
            "Click now to get started and subscribe. "
            "See the beautiful dashboard with clear visual data. "
            "Don't miss this exclusive limited offer!"
        )
        result = score_transcript(text)
        assert 0.0 <= result["A5"] <= 1.0
        assert 0.0 <= result["LO"] <= 1.0
        assert 0.0 <= result["Area45"] <= 1.0
        assert 0.0 <= result["TPJ"] <= 1.0
