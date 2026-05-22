from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np


@dataclass
class ROIScores:
    A5: float
    LO: float
    Area45: float
    TPJ: float


class ROIExtractor:
    """
    Extracts Region-of-Interest scores from neural predictions.

    Maps ~20k fsaverage5 vertices to 4 key brain regions:
    - A5: Primary Auditory Cortex (temporal)
    - LO: Lateral Occipital (visual processing)
    - Area45: Inferior Frontal Gyrus (valuation/reward)
    - TPJ: Temporo-Parietal Junction (social cognition)
    """

    FS_AVERAGE5_VERTICES = 20484

    ROI_INDICES = {
        "A5": {
            "name": "Primary Auditory Cortex",
            "start": 4200,
            "end": 4600,
            "description": "Audio stickiness, sound processing",
        },
        "LO": {
            "name": "Lateral Occipital",
            "start": 8000,
            "end": 9200,
            "description": "Visual hook strength",
        },
        "Area45": {
            "name": "Inferior Frontal Gyrus (BA45)",
            "start": 12000,
            "end": 12800,
            "description": "Perceived utility/reward valuation",
        },
        "TPJ": {
            "name": "Temporo-Parietal Junction",
            "start": 14000,
            "end": 15200,
            "description": "Emotional resonance, social cognition",
        },
    }

    @staticmethod
    def extract_from_predictions(
        predictions: np.ndarray, roi_indices: Optional[Dict] = None
    ) -> ROIScores:
        if isinstance(predictions, list):
            predictions = np.array(predictions)

        if predictions.ndim == 1:
            predictions = predictions[np.newaxis, :]

        roi_map = roi_indices or ROIExtractor.ROI_INDICES
        scores = {}

        for roi_name, roi_info in roi_map.items():
            start = roi_info["start"]
            end = roi_info["end"]

            if end <= predictions.shape[-1]:
                roi_activations = predictions[..., start:end]
                mean_activation = float(np.mean(roi_activations))
                scores[roi_name] = round(float(np.clip(mean_activation, 0, 1)), 4)
            else:
                scores[roi_name] = 0.5

        return ROIScores(
            A5=scores["A5"], LO=scores["LO"], Area45=scores["Area45"], TPJ=scores["TPJ"]
        )

    @staticmethod
    def extract_with_temporal_dynamics(
        predictions: np.ndarray, n_segments: int = 4
    ) -> Dict[str, Any]:
        if isinstance(predictions, list):
            predictions = np.array(predictions)

        if predictions.ndim == 1:
            predictions = predictions[np.newaxis, :]

        n_timesteps = predictions.shape[0]
        segment_size = max(1, n_timesteps // n_segments)

        temporal_roi = {}
        for i in range(n_segments):
            start = i * segment_size
            end = min((i + 1) * segment_size, n_timesteps)
            segment_preds = predictions[start:end]

            roi = ROIExtractor.extract_from_predictions(segment_preds)
            temporal_roi[f"segment_{i}"] = {
                "time_range": f"{start}-{end}",
                "A5": roi.A5,
                "LO": roi.LO,
                "Area45": roi.Area45,
                "TPJ": roi.TPJ,
            }

        overall = ROIExtractor.extract_from_predictions(predictions)

        return {
            "overall": {
                "A5": overall.A5,
                "LO": overall.LO,
                "Area45": overall.Area45,
                "TPJ": overall.TPJ,
            },
            "temporal": temporal_roi,
            "n_segments": n_segments,
        }

    @staticmethod
    def get_roi_metadata() -> Dict[str, Any]:
        return {
            roi_name: {
                "name": info["name"],
                "description": info["description"],
                "vertex_range": f"{info['start']}-{info['end']}",
            }
            for roi_name, info in ROIExtractor.ROI_INDICES.items()
        }


roi_extractor = ROIExtractor()
