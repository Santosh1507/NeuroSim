"""
Tests for TribeV2 API endpoint: preload, status, predict, and path validation.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from flask import Flask

from app.api.tribev2 import tribev2_bp, _validate_path, get_tribe_model


@pytest.fixture
def app():
    """Create a test Flask app with TribeV2 blueprint."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(tribev2_bp, url_prefix='/api/tribev2')
    return app


@pytest.fixture(autouse=True)
def mock_auth():
    """Mock verify_auth to return None (success) for all tests."""
    with patch('app.api.verify_auth', return_value=None):
        yield


@pytest.fixture
def reset_tribev2():
    """Reset TribeV2 module state before each test."""
    import app.api.tribev2 as tribev2_module
    tribev2_module._TRIBE_MODEL = None
    tribev2_module._MODEL_LOADING = False
    tribev2_module._MODEL_ERROR = None
    yield


class TestValidatePath:
    """Tests for the _validate_path() security function."""

    def test_allows_path_within_media_dir(self, tmp_path):
        """Accepts paths within the allowed media directory."""
        media_dir = tmp_path / 'media'
        media_dir.mkdir()
        test_file = media_dir / 'video.mp4'
        test_file.touch()

        import app.api.tribev2 as tribev2_module
        original_dirs = tribev2_module._ALLOWED_BASE_DIRS
        tribev2_module._ALLOWED_BASE_DIRS = [media_dir.resolve()]

        try:
            resolved, err = _validate_path(str(test_file))
            assert err is None
            assert resolved == test_file.resolve()
        finally:
            tribev2_module._ALLOWED_BASE_DIRS = original_dirs

    def test_rejects_path_traversal(self, tmp_path):
        """Rejects paths that escape the allowed directory via ../."""
        media_dir = tmp_path / 'media'
        media_dir.mkdir()
        # Create a file outside the media dir
        outside_file = tmp_path.parent / 'outside.txt'
        outside_file.touch()

        import app.api.tribev2 as tribev2_module
        original_dirs = tribev2_module._ALLOWED_BASE_DIRS
        tribev2_module._ALLOWED_BASE_DIRS = [media_dir.resolve()]

        try:
            resolved, err = _validate_path(str(outside_file))
            assert err is not None
            _, status = err
            assert status == 403
        finally:
            tribev2_module._ALLOWED_BASE_DIRS = original_dirs

    def test_rejects_absolute_path_outside_allowed(self, tmp_path):
        """Rejects absolute paths outside allowed directories."""
        media_dir = tmp_path / 'media'
        media_dir.mkdir()
        # Use a completely different directory
        other_dir = tmp_path.parent / 'other'
        other_dir.mkdir(exist_ok=True)
        evil_file = other_dir / 'evil.sh'
        evil_file.touch()

        import app.api.tribev2 as tribev2_module
        original_dirs = tribev2_module._ALLOWED_BASE_DIRS
        tribev2_module._ALLOWED_BASE_DIRS = [media_dir.resolve()]

        try:
            resolved, err = _validate_path(str(evil_file))
            assert err is not None
            _, status = err
            assert status == 403
        finally:
            tribev2_module._ALLOWED_BASE_DIRS = original_dirs


class TestStatus:
    """Tests for the /api/tribev2/status endpoint."""

    def test_status_when_not_loaded(self, app, reset_tribev2):
        """Returns loaded=false when model is not loaded."""
        with app.test_client() as client:
            resp = client.get('/api/tribev2/status')
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True
            assert data['data']['loaded'] is False
            assert data['data']['loading'] is False

    def test_status_when_loading(self, app, reset_tribev2):
        """Returns loading=true when model is being loaded."""
        import app.api.tribev2 as tribev2_module
        tribev2_module._MODEL_LOADING = True

        with app.test_client() as client:
            resp = client.get('/api/tribev2/status')
            data = resp.get_json()
            assert data['data']['loading'] is True

    def test_status_when_loaded(self, app, reset_tribev2):
        """Returns loaded=true when model is ready."""
        import app.api.tribev2 as tribev2_module
        tribev2_module._TRIBE_MODEL = MagicMock()

        with app.test_client() as client:
            resp = client.get('/api/tribev2/status')
            data = resp.get_json()
            assert data['data']['loaded'] is True


class TestPreload:
    """Tests for the /api/tribev2/preload endpoint."""

    def test_preload_starts_loading(self, app, reset_tribev2):
        """Returns loading_started when model is not yet loading."""
        with app.test_client() as client:
            resp = client.post('/api/tribev2/preload')
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['data']['status'] == 'loading_started'

    def test_preload_when_already_loaded(self, app, reset_tribev2):
        """Returns already_loaded when model is ready."""
        import app.api.tribev2 as tribev2_module
        tribev2_module._TRIBE_MODEL = MagicMock()

        with app.test_client() as client:
            resp = client.post('/api/tribev2/preload')
            data = resp.get_json()
            assert data['data']['status'] == 'already_loaded'

    def test_preload_when_loading_in_progress(self, app, reset_tribev2):
        """Returns loading_in_progress when already loading."""
        import app.api.tribev2 as tribev2_module
        tribev2_module._MODEL_LOADING = True

        with app.test_client() as client:
            resp = client.post('/api/tribev2/preload')
            data = resp.get_json()
            assert data['data']['status'] == 'loading_in_progress'


class TestPredict:
    """Tests for the /api/tribev2/predict endpoint."""

    def test_predict_without_path(self, app, reset_tribev2):
        """Returns 400 when no path is provided."""
        with app.test_client() as client:
            resp = client.post('/api/tribev2/predict', json={})
            assert resp.status_code == 400
            data = resp.get_json()
            assert 'Provide video_path' in data['error']

    def test_predict_when_model_not_loaded(self, app, reset_tribev2, tmp_path):
        """Returns 503 when model is not loaded."""
        # Create a valid path within the allowed directory
        media_dir = tmp_path / 'media'
        media_dir.mkdir()
        test_file = media_dir / 'test.mp4'
        test_file.touch()

        import app.api.tribev2 as tribev2_module
        tribev2_module._ALLOWED_BASE_DIRS = [media_dir.resolve()]

        with app.test_client() as client:
            resp = client.post('/api/tribev2/predict', json={'video_path': str(test_file)})
            assert resp.status_code == 503
            data = resp.get_json()
            assert 'not loaded' in data['error']

    def test_predict_successful(self, app, reset_tribev2):
        """Returns prediction results when model is loaded and path is valid."""
        import app.api.tribev2 as tribev2_module
        import numpy as np

        mock_model = MagicMock()
        mock_df = MagicMock()
        mock_model.get_events_dataframe.return_value = mock_df
        mock_preds = np.zeros((10, 100))
        mock_model.predict.return_value = (mock_preds, [0, 5, 10])
        tribev2_module._TRIBE_MODEL = mock_model

        with patch('app.api.tribev2._validate_path', return_value=(Path('/app/media/test.mp4'), None)):
            with app.test_client() as client:
                resp = client.post('/api/tribev2/predict', json={'video_path': '/app/media/test.mp4'})
                assert resp.status_code == 200
                data = resp.get_json()
                assert data['success'] is True
                assert data['data']['n_timesteps'] == 10
                assert data['data']['n_vertices'] == 100

    def test_predict_path_validation_failure(self, app, reset_tribev2):
        """Returns 403 when path validation fails."""
        import app.api.tribev2 as tribev2_module
        tribev2_module._TRIBE_MODEL = MagicMock()

        with patch('app.api.tribev2._validate_path', return_value=(None, ('Path not allowed', 403))):
            with app.test_client() as client:
                resp = client.post('/api/tribev2/predict', json={'video_path': '/etc/passwd'})
                assert resp.status_code == 403
                data = resp.get_json()
                assert 'not allowed' in data['error']
