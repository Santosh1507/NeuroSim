import numpy as np

from roi_extractor import ROIExtractor, ROIScores


class TestROIExtractor:
    def test_extract_from_predictions_2d(self):
        predictions = np.random.uniform(0, 1, size=(20, 20484))
        roi = ROIExtractor.extract_from_predictions(predictions)
        assert isinstance(roi, ROIScores)
        assert 0 <= roi.A5 <= 1
        assert 0 <= roi.LO <= 1
        assert 0 <= roi.Area45 <= 1
        assert 0 <= roi.TPJ <= 1

    def test_extract_from_predictions_1d(self):
        predictions = np.random.uniform(0, 1, size=20484)
        roi = ROIExtractor.extract_from_predictions(predictions)
        assert isinstance(roi, ROIScores)

    def test_extract_from_predictions_list(self):
        predictions = np.random.uniform(0, 1, size=(10, 20484)).tolist()
        roi = ROIExtractor.extract_from_predictions(predictions)
        assert isinstance(roi, ROIScores)

    def test_roi_indices_are_valid(self):
        for name, info in ROIExtractor.ROI_INDICES.items():
            assert info["start"] < info["end"]
            assert info["end"] <= ROIExtractor.FS_AVERAGE5_VERTICES

    def test_temporal_dynamics(self):
        predictions = np.random.uniform(0, 1, size=(20, 20484))
        result = ROIExtractor.extract_with_temporal_dynamics(predictions, n_segments=4)
        assert "overall" in result
        assert "temporal" in result
        assert result["n_segments"] == 4
        assert "A5" in result["overall"]
        assert "LO" in result["overall"]

    def test_roi_metadata(self):
        metadata = ROIExtractor.get_roi_metadata()
        assert "A5" in metadata
        assert "LO" in metadata
        assert "Area45" in metadata
        assert "TPJ" in metadata
        for name, info in metadata.items():
            assert "name" in info
            assert "description" in info
