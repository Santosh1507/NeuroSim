"""Tests for transcriber module.

faster-whisper may or may not be installed in the test environment.
Tests handle both cases gracefully.
"""

from transcriber import transcriber


class TestTranscriberCore:
    """Tests that work regardless of whisper availability."""

    def test_available_property(self):
        """available should be a bool."""
        assert isinstance(transcriber.available, bool)

    def test_transcribe_empty_on_nonexistent_file(self):
        """Transcribing a nonexistent file returns empty string."""
        result = transcriber.transcribe("/nonexistent/audio.mp3")
        assert result == ""

    def test_unload_does_not_crash(self):
        """unload() should be safe to call even when no model is loaded."""
        transcriber.unload()
        # No exception = pass

    def test_double_unload_is_safe(self):
        """Calling unload() twice should not raise."""
        transcriber.unload()
        transcriber.unload()

    def test_transcribe_empty_empty_string(self):
        """Edge case: empty string path returns empty string."""
        result = transcriber.transcribe("")
        assert result == ""

    def test_model_size_default(self):
        assert transcriber.model_size == "tiny"

    def test_compute_type_default(self):
        assert transcriber.compute_type == "int8"
