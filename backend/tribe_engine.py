import asyncio
import os
import time
from typing import Any, Dict, Optional

import numpy as np

from config import settings


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
                print("TRIBE v2 loaded from HuggingFace (GPU mode)")
            except Exception as e:
                print(f"TRIBE v2 load failed: {e}. Falling back to simulated mode.")
                self.is_real = False

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

    async def _simulated_predict(
        self, video_path: str, seed: Optional[int] = None
    ) -> Dict[str, Any]:
        await asyncio.sleep(1.5)

        # Use a random seed by default so each run produces unique predictions.
        # Accept an explicit seed for testing/deterministic mode.
        if seed is not None:
            np.random.seed(seed % (2**32))
        else:
            np.random.seed((time.time_ns() ^ int.from_bytes(os.urandom(4), "big")) % (2**32))

        n_timesteps = 20
        n_vertices = 20484

        base_activation = np.random.uniform(0.3, 0.7, size=(n_timesteps, n_vertices))

        temporal_pattern = np.sin(np.linspace(0, 4 * np.pi, n_timesteps))
        temporal_pattern = (temporal_pattern + 1) / 2
        temporal_pattern = temporal_pattern[:, np.newaxis]

        predictions = base_activation * temporal_pattern * 0.5 + 0.25
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
        }

    async def predict_from_text(self, text: str, seed: Optional[int] = None) -> Dict[str, Any]:
        if self.is_real and self.model:
            df = self.model.get_events_dataframe(text_path=text)
            preds, segments = self.model.predict(events=df)
            return {"predictions": preds, "segments": segments, "mode": "real"}

        await asyncio.sleep(0.8)
        if seed is not None:
            np.random.seed(seed % (2**32))
        else:
            np.random.seed((time.time_ns() ^ int.from_bytes(os.urandom(4), "big")) % (2**32))
        return {
            "predictions": np.random.uniform(0.2, 0.8, size=(10, 20484)).tolist(),
            "segments": [{"start": 0, "end": len(text), "type": "text"}],
            "mode": "simulated",
        }


tribe_engine = TribeEngine()
