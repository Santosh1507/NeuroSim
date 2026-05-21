"""Tests for signal_merge module."""

from signal_merge import get_analysis_mode, merge_signals


class TestMergeSignals:
    def test_vision_disabled_returns_heuristic(self):
        heuristic = {"A5": 0.7, "LO": 0.6, "Area45": 0.5, "TPJ": 0.8}
        vision = {"mode": "disabled", "error": "no key"}
        result = merge_signals(heuristic, vision)
        assert result.A5 == 0.7
        assert result.LO == 0.6
        assert result.Area45 == 0.5
        assert result.TPJ == 0.8

    def test_vision_error_returns_heuristic(self):
        heuristic = {"A5": 0.6, "LO": 0.5, "Area45": 0.4, "TPJ": 0.7}
        vision = {"mode": "error", "error": "timeout"}
        result = merge_signals(heuristic, vision)
        assert result.A5 == 0.6

    def test_vision_fallback_merges_with_heuristic(self):
        heuristic = {"A5": 0.65, "LO": 0.55, "Area45": 0.45, "TPJ": 0.75}
        vision = {
            "mode": "fallback",
            "audio_engagement": 0.35,
            "visual_engagement": 0.45,
            "cta_presence": 0.55,
            "emotional_arc": 0.65,
        }
        result = merge_signals(heuristic, vision)
        assert result.A5 == 0.485
        assert result.LO == 0.485

    def test_vision_dominates_when_both_available(self):
        heuristic = {"A5": 0.3, "LO": 0.3, "Area45": 0.3, "TPJ": 0.3}
        vision = {
            "mode": "vision",
            "audio_engagement": 0.9,
            "visual_engagement": 0.9,
            "cta_presence": 0.9,
            "emotional_arc": 0.9,
        }
        result = merge_signals(heuristic, vision)
        # Vision dominates: 0.55*0.9 + 0.45*0.3 = 0.63
        assert result.A5 == 0.63
        # 0.65*0.9 + 0.35*0.3 = 0.69
        assert result.LO == 0.69
        # 0.60*0.9 + 0.40*0.3 = 0.66
        assert result.Area45 == 0.66
        # 0.55*0.9 + 0.45*0.3 = 0.63
        assert result.TPJ == 0.63

    def test_missing_vision_keys_use_defaults(self):
        heuristic = {"A5": 0.5, "LO": 0.5, "Area45": 0.5, "TPJ": 0.5}
        vision = {"mode": "vision"}
        result = merge_signals(heuristic, vision)
        # All vision keys default to 0.5, heuristic is 0.5, so result is 0.5
        assert result.A5 == 0.5

    def test_clamped_to_valid_range(self):
        heuristic = {"A5": 1.0, "LO": 1.0, "Area45": 1.0, "TPJ": 1.0}
        vision = {
            "mode": "vision",
            "audio_engagement": 1.0,
            "visual_engagement": 1.0,
            "cta_presence": 1.0,
            "emotional_arc": 1.0,
        }
        result = merge_signals(heuristic, vision)
        assert result.A5 <= 1.0
        assert result.LO <= 1.0
        assert result.Area45 <= 1.0
        assert result.TPJ <= 1.0


class TestGetAnalysisMode:
    def test_vision_and_heuristic(self):
        assert get_analysis_mode(True, "vision") == "vision+heuristic"

    def test_vision_only(self):
        assert get_analysis_mode(False, "vision") == "vision"

    def test_heuristic_only(self):
        assert get_analysis_mode(True, "disabled") == "heuristic"

    def test_fallback_and_heuristic(self):
        assert get_analysis_mode(True, "fallback") == "fallback+heuristic"

    def test_fallback_only(self):
        assert get_analysis_mode(False, "fallback") == "fallback"

    def test_unknown(self):
        assert get_analysis_mode(False, "error") == "unknown"
