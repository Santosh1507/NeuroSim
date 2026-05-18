"""
Tests for NeuroSim API auth protection and async job contracts.
"""

from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from flask import Flask

from app.api import neurosim_bp
import app.api.neurosim as neurosim_module


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(neurosim_bp, url_prefix='/api/neurosim')
    return app


@pytest.fixture
def neurosim_tmp_dirs(tmp_path, monkeypatch):
    upload_dir = tmp_path / 'uploads'
    job_dir = tmp_path / 'jobs'
    upload_dir.mkdir()
    job_dir.mkdir()
    monkeypatch.setattr(neurosim_module, 'UPLOAD_DIR', upload_dir)
    monkeypatch.setattr(neurosim_module, 'VIDEO_JOB_DIR', job_dir)
    return upload_dir, job_dir


def _video(name='sample.mp4'):
    return BytesIO(b'fake video bytes'), name


def test_neurosim_routes_require_auth(app):
    with app.test_client() as client:
        resp = client.get('/api/neurosim/experiments')
        assert resp.status_code == 401
        assert resp.get_json()['success'] is False


def test_upload_returns_video_id_and_persistent_processing_status(app, neurosim_tmp_dirs, monkeypatch):
    monkeypatch.setattr(neurosim_module, '_start_background_thread', lambda *args: None)

    with patch('app.api.verify_auth', return_value=None):
        with app.test_client() as client:
            resp = client.post(
                '/api/neurosim/upload',
                data={'video': _video()},
                content_type='multipart/form-data',
            )

            assert resp.status_code == 200
            data = resp.get_json()
            assert data['status'] == 'processing'
            assert data['video_id'].startswith('video_')

            status_resp = client.get(f"/api/neurosim/video/{data['video_id']}/status")
            assert status_resp.status_code == 200
            status = status_resp.get_json()
            assert status['status'] == 'processing'
            assert status['video_id'] == data['video_id']
            assert 'path' not in status

            _, job_dir = neurosim_tmp_dirs
            assert Path(job_dir / f"{data['video_id']}.json").exists()


def test_multipart_ab_test_returns_experiment_id_immediately(app, neurosim_tmp_dirs, monkeypatch):
    monkeypatch.setattr(neurosim_module, '_start_background_thread', lambda *args: None)

    with patch('app.api.verify_auth', return_value=None):
        with app.test_client() as client:
            resp = client.post(
                '/api/neurosim/ab-test',
                data={
                    'video_a': _video('a.mp4'),
                    'video_b': _video('b.mp4'),
                    'context': 'predict social performance',
                },
                content_type='multipart/form-data',
            )

            assert resp.status_code == 200
            data = resp.get_json()
            assert data['status'] == 'processing'
            assert data['experiment_id'].startswith('ab_')

            results_resp = client.get(f"/api/neurosim/ab-test/{data['experiment_id']}/results")
            assert results_resp.status_code == 200
            results = results_resp.get_json()
            assert results['status'] == 'processing'
            assert results['message'] == 'Video processing still running'
