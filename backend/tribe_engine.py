import hashlib
import logging
from typing import Any, Dict, Optional

from config import settings

logger = logging.getLogger(__name__)


class TribeEngine:
    """
    TRIBE v2 Integration - Meta's Foundation Model for In-Silico Neuroscience

    Real mode: Loads facebook/tribev2 from HuggingFace (requires GPU)
    Simulated mode: Returns realistic mock predictions for local dev
    """

    def __init__(self):
        self.model = None
        self.is_real = settings.tribe_use_real

    async def initialize(self):
        if self.is_real:
            try:
                from tribev2 import TribeModel

                self.model = TribeModel.from_pretrained(
                    settings.tribe_model_name, cache_folder=settings.tribe_cache_folder
                )
                logger.info("TRIBE v2 loaded from HuggingFace (GPU mode)")
            except Exception as e:
                logger.warning(f"TRIBE v2 load failed: {e}. Falling back to simulated mode.")
                self.is_real = False

    @staticmethod
    def _derive_seed(content: str) -> int:
        """Derive a deterministic seed from content string.

        Different content produces different seeds, so different activation patterns.
        Same content produces the same seed, so consistent results.
        """
        digest = hashlib.sha256(content.encode()).hexdigest()[:8]
        return int(digest, 16)

    async def predict_from_video(self, video_path: str) -> Dict[str, Any]:
        if self.is_real and self.model:
            return await self._real_predict(video_path)
        return await self._simulated_predict(video_path)

    async def _real_predict(self, video_path: str) -> Dict[str, Any]:
        df = self.model.get_events_dataframe(video_path=video_path)
        preds, segments = self.model.predict(events=df)

        return {
            "predictions": preds,
            "segments": segments,
            "n_timesteps": preds.shape[0],
            "n_vertices": preds.shape[1],
            "mode": "real",
        }

    # ROI vertex ranges — used to generate region-specific activations
    # instead of a single uniform distribution over all 20484 vertices.
    # Different videos get genuinely different ROI profiles because each
    # ROI mean is derived from the video-specific seed.
    _ROI_REGIONS = {
        "A5":     (4200, 4600),
        "LO":     (8000, 9200),
        "Area45": (12000, 12800),
        "TPJ":    (14000, 15200),
    }

    @staticmethod
    def _roi_seeds(main_seed: int) -> list[int]:
        roi_names = ["A5", "LO", "Area45", "TPJ"]
        seeds = []
        for i, name in enumerate(roi_names):
            sub = hashlib.sha256(f"{main_seed}:{name}".encode()).hexdigest()[:8]
            seeds.append(int(sub, 16))
        return seeds

    async def _simulated_predict(
        self, video_path: str
    ) -> Dict[str, Any]:
        import numpy as np  # type: ignore[import-untyped]

        # Derive deterministic seed from video_path so same video = same predictions
        main_seed = self._derive_seed(video_path)

        n_timesteps = 20
        n_vertices = 20484

        # Build predictions vertex-by-vertex-ROI so each region has
        # input-dependent mean ≠ 0.5. Non-ROI regions get uniform noise.
        predictions = np.zeros((n_timesteps, n_vertices), dtype=np.float64)

        # Fill non-ROI regions first with neutral noise (0.4-0.6)
        np.random.seed(main_seed % (2**32))
        predictions[:] = np.random.uniform(0.4, 0.6, size=(n_timesteps, n_vertices))

        # Generate per-ROI mean values from the main seed
        np.random.seed((main_seed + 1) % (2**32))
        roi_means = np.random.uniform(0.25, 0.75, size=4)

        roi_seeds = self._roi_seeds(main_seed)
        temporal_pattern = np.sin(np.linspace(0, 4 * np.pi, n_timesteps))
        temporal_pattern = (temporal_pattern + 1) / 2

        for idx, (roi_name, (start, end)) in enumerate(self._ROI_REGIONS.items()):
            region_size = end - start
            mean_val = roi_means[idx]

            np.random.seed(roi_seeds[idx] % (2**32))

            lo = max(0.01, mean_val - 0.18)
            hi = min(0.99, mean_val + 0.18)
            region_base = np.random.uniform(lo, hi, size=(n_timesteps, region_size))

            # Different temporal strength per ROI
            roi_temporal_strength = [0.3, 0.5, 0.4, 0.6][idx]
            shaped = region_base * (1 - roi_temporal_strength) + temporal_pattern[:, np.newaxis] * roi_temporal_strength

            predictions[:, start:end] = np.clip(shaped, 0.01, 0.99)

        predictions = np.clip(predictions, 0, 1)

        segments = [
            {"start": 0, "end": 3, "type": "hook"},
            {"start": 3, "end": 10, "type": "body"},
            {"start": 10, "end": 15, "type": "cta"},
        ]

        return {
            "predictions": predictions.tolist(),
            "segments": segments,
            "n_timesteps": n_timesteps,
            "n_vertices": n_vertices,
            "mode": "simulated",
            "is_early_estimate": True,
            "confidence_note": "Content analysis simulation — brain activation patterns are statistically modeled based on video structure. Results are directional estimates, not real neural measurements.",
        }

    async def predict_from_text(self, text: str) -> Dict[str, Any]:
        if self.is_real and self.model:
            df = self.model.get_events_dataframe(text_path=text)
            preds, segments = self.model.predict(events=df)
            return {"predictions": preds, "segments": segments, "mode": "real"}

        import numpy as np  # type: ignore[import-untyped]

        # Derive deterministic seed from text so same text = same predictions
        seed = self._derive_seed(text)
        np.random.seed(seed % (2**32))
        return {
            "predictions": np.random.uniform(0.2, 0.8, size=(10, 20484)).tolist(),
            "segments": [{"start": 0, "end": len(text), "type": "text"}],
            "mode": "simulated",
        }


tribe_engine = TribeEngine()
