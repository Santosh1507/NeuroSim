"""Audio transcription using faster-whisper (tiny model).

Fits within Render's 512MB free tier:
  - tiny model: 75MB on disk, ~150MB loaded
  - Leaves ~350MB for FastAPI + numpy + heuristic scorer
"""

import os

try:
    from faster_whisper import WhisperModel

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    WhisperModel = None


class Transcriber:
    """faster-whisper transcription with lazy model loading."""

    def __init__(self, model_size: str = "tiny", compute_type: str = "int8"):
        self.model_size = model_size
        self.compute_type = compute_type
        self._model = None

    @property
    def available(self) -> bool:
        return WHISPER_AVAILABLE

    def _load_model(self):
        if self._model is None and WHISPER_AVAILABLE:
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type=self.compute_type,
                download_root=os.path.join(os.path.dirname(__file__), ".whisper_cache"),
            )
        return self._model

    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file and return full text.

        Returns empty string if whisper is unavailable or transcription fails.
        """
        model = self._load_model()
        if model is None:
            return ""

        try:
            segments, _ = model.transcribe(
                audio_path,
                beam_size=1,
                language="en",
                vad_filter=False,
            )
            return " ".join(seg.text for seg in segments).strip()
        except Exception as e:
            print(f"Transcription failed: {e}")
            return ""

    def unload(self):
        """Free model from memory."""
        import gc

        self._model = None
        gc.collect()


transcriber = Transcriber()
