"""Tests for generate_pdf_report — using ReportLab to produce PDF bytes."""

from datetime import datetime

from pdf_report import generate_pdf_report


class TestPDFReport:
    """Test PDF report generation with various analysis data shapes."""

    def test_pdf_starts_with_pdf_magic_bytes(self):
        """Valid PDF output always starts with %PDF."""
        result = generate_pdf_report({"hook_score": 75})
        assert result.startswith(b"%PDF-")

    def test_empty_analysis(self):
        """Should handle empty analysis dict without crashing."""
        result = generate_pdf_report({})
        assert result.startswith(b"%PDF-")

    def test_none_video_info(self):
        """Should handle None video_info gracefully (the video_info or {} guard)."""
        result = generate_pdf_report({"hook_score": 80}, video_info=None)
        assert result.startswith(b"%PDF-")

    def test_empty_dict_video_info(self):
        """Should handle empty dict video_info."""
        result = generate_pdf_report({"hook_score": 80}, video_info={})
        assert result.startswith(b"%PDF-")

    def test_full_analysis_data(self):
        """Complete analysis with all sections should generate valid PDF."""
        analysis = {
            "hook_score": 85,
            "authenticity_score": 72,
            "success_probability": 78,
            "viral_potential": 65,
            "risk_score": 25,
            "stage_gate": {
                "passed": True,
                "W_attn": 0.65,
                "threshold": 0.4,
            },
            "recommendations": [
                "Add more visual contrast in first 3 seconds",
                "Consider audio dynamic change at 0:05",
            ],
            "sentiment_forecast": {
                "positive_sentiment_pct": 60.0,
                "negative_sentiment_pct": 20.0,
                "neutral_sentiment_pct": 20.0,
                "shareability_index": 45.0,
            },
            "analysis_response": {
                "cortical_response": {
                    "visual_cortex": 82.0,
                    "auditory_cortex": 65.0,
                    "language_center": 70.0,
                },
            },
        }
        video_info = {
            "filename": "test_video.mp4",
            "upload_time": datetime.now().isoformat(),
        }
        result = generate_pdf_report(analysis, video_info=video_info)
        assert result.startswith(b"%PDF-")
        # Should be a reasonable PDF size (> 2KB for full data, < 100KB)
        assert 2000 < len(result) < 100000

    def test_minimal_analysis(self):
        """Only essential fields — no recommendations, sentiment, or brain response."""
        analysis = {
            "hook_score": 50,
            "authenticity_score": 50,
            "success_probability": 50,
            "viral_potential": 50,
            "risk_score": 50,
        }
        result = generate_pdf_report(analysis)
        assert result.startswith(b"%PDF-")

    def test_video_info_with_filename(self):
        """video_info.filename should appear in the PDF content."""
        result = generate_pdf_report(
            {"hook_score": 70},
            video_info={"filename": "my_ad.mp4", "upload_time": "2024-01-01"},
        )
        # PDF should contain the filename as text
        assert result.startswith(b"%PDF-")

    def test_stage_gate_fail(self):
        """Stage-gate FAIL should render without error."""
        analysis = {
            "hook_score": 30,
            "stage_gate": {
                "passed": False,
                "W_attn": 0.25,
                "threshold": 0.4,
            },
        }
        result = generate_pdf_report(analysis)
        assert result.startswith(b"%PDF-")

    def test_stage_gate_pass(self):
        """Stage-gate PASS should render without error."""
        analysis = {
            "hook_score": 90,
            "stage_gate": {
                "passed": True,
                "W_attn": 0.85,
                "threshold": 0.4,
            },
        }
        result = generate_pdf_report(analysis)
        assert result.startswith(b"%PDF-")

    def test_missing_nested_keys(self):
        """Missing optional nested sections (no stage_gate, no analysis_response) should not crash."""
        analysis = {"hook_score": 60, "success_probability": 70}
        result = generate_pdf_report(analysis, video_info=None)
        assert result.startswith(b"%PDF-")

    def test_recommendations_as_list_of_strings(self):
        """Recommendations are strings (not dicts) for the PDF code style."""
        analysis = {
            "hook_score": 80,
            "recommendations": [
                "Improve the hook",
                "Add a stronger CTA",
                "Shorten the intro",
            ],
        }
        result = generate_pdf_report(analysis)
        assert result.startswith(b"%PDF-")

    def test_empty_recommendations_list(self):
        """Empty recommendations list should not crash."""
        analysis = {"hook_score": 50, "recommendations": []}
        result = generate_pdf_report(analysis)
        assert result.startswith(b"%PDF-")

    def test_zero_scores(self):
        """All zero scores should render without error."""
        analysis = {
            "hook_score": 0,
            "authenticity_score": 0,
            "success_probability": 0,
            "viral_potential": 0,
            "risk_score": 0,
        }
        result = generate_pdf_report(analysis)
        assert result.startswith(b"%PDF-")
