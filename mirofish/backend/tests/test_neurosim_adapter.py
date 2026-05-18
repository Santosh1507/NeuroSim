"""
Tests for NeuroSim adapter endpoint: agent capping, response fields, error handling.
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask

from app.api import simulation_bp


@pytest.fixture
def app():
    """Create a test Flask app with simulation blueprint."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    return app


@pytest.fixture(autouse=True)
def mock_auth():
    """Mock verify_auth to return None (success) for all tests."""
    with patch('app.api.verify_auth', return_value=None):
        yield


class TestNeuroSimAgentCapping:
    """Tests for agent count capping behavior."""

    def test_caps_agents_at_200(self, app):
        """Caps requested agents at 200 and reports it."""
        with app.test_client() as client:
            resp = client.post('/api/simulation', json={
                'seed_material': 'test content',
                'num_agents': 1000
            })
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['num_agents'] == 200
            assert data['num_agents_requested'] == 1000
            assert data['max_agents'] == 200

    def test_accepts_under_cap(self, app):
        """Accepts agent count under the cap without modification."""
        with app.test_client() as client:
            resp = client.post('/api/simulation', json={
                'seed_material': 'test content',
                'num_agents': 50
            })
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['num_agents'] == 50
            assert data['num_agents_requested'] == 50

    def test_default_agents_when_not_specified(self, app):
        """Uses default of 1000 (capped to 200) when num_agents not provided."""
        with app.test_client() as client:
            resp = client.post('/api/simulation', json={
                'seed_material': 'test content'
            })
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['num_agents'] == 200
            assert data['num_agents_requested'] == 1000


class TestNeuroSimResponse:
    """Tests for response structure and fields."""

    def test_response_has_all_required_fields(self, app):
        """Response includes all expected fields."""
        with app.test_client() as client:
            resp = client.post('/api/simulation', json={
                'seed_material': 'test content',
                'num_agents': 100,
                'simulation_rounds': 5
            })
            assert resp.status_code == 200
            data = resp.get_json()

            required_fields = [
                'simulation_id', 'mode', 'persona_distribution',
                'final_sentiment', 'viral_prediction', 'backlash_prediction',
                'share_prediction', 'trust_trajectory', 'comment_samples',
                'simulation_rounds', 'num_agents'
            ]
            for field in required_fields:
                assert field in data, f"Missing field: {field}"

    def test_mode_is_real(self, app):
        """Response mode is 'real' (not simulated fallback)."""
        with app.test_client() as client:
            resp = client.post('/api/simulation', json={
                'seed_material': 'test content'
            })
            data = resp.get_json()
            assert data['mode'] == 'real'

    def test_sentiment_is_percentage(self, app):
        """Final sentiment is scaled to 0-100 range."""
        with app.test_client() as client:
            resp = client.post('/api/simulation', json={
                'seed_material': 'test content'
            })
            data = resp.get_json()
            assert 0 <= data['final_sentiment'] <= 100


class TestNeuroSimErrorHandling:
    """Tests for error scenarios."""

    def test_empty_request(self, app):
        """Handles empty JSON body gracefully."""
        with app.test_client() as client:
            resp = client.post('/api/simulation', json={})
            # Should still work with defaults
            assert resp.status_code == 200

    def test_caps_rounds_at_10(self, app):
        """Caps simulation rounds at 10."""
        with app.test_client() as client:
            resp = client.post('/api/simulation', json={
                'seed_material': 'test content',
                'simulation_rounds': 50
            })
            data = resp.get_json()
            assert data['simulation_rounds'] == 10


class TestGeneratePersonas:
    """Tests for persona generation and seed reproducibility."""

    def test_personas_have_correct_structure(self, app):
        """Generated personas produce non-empty distribution."""
        with app.test_client() as client:
            resp = client.post('/api/simulation', json={
                'seed_material': 'test', 'num_agents': 10
            })
            data = resp.get_json()
            assert len(data['persona_distribution']) > 0

    def test_seed_produces_reproducible_results(self, app):
        """Same seed produces identical final_sentiment."""
        with app.test_client() as client:
            resp1 = client.post('/api/simulation', json={
                'seed_material': 'test', 'num_agents': 50,
                'simulation_rounds': 5, 'seed': 42
            })
            resp2 = client.post('/api/simulation', json={
                'seed_material': 'test', 'num_agents': 50,
                'simulation_rounds': 5, 'seed': 42
            })
            data1 = resp1.get_json()
            data2 = resp2.get_json()
            assert data1['final_sentiment'] == data2['final_sentiment']
            assert data1['seed_used'] == 42

    def test_seed_used_field_present(self, app):
        """Response includes seed_used field."""
        with app.test_client() as client:
            resp = client.post('/api/simulation', json={
                'seed_material': 'test', 'num_agents': 10
            })
            data = resp.get_json()
            assert 'seed_used' in data
            assert data['seed_used'] is None
