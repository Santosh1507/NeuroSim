"""
Tests for Supabase JWT authentication decorator and verify_auth helper.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, request

from app.auth import require_auth, verify_auth, _get_supabase_admin


@pytest.fixture
def app():
    """Create a test Flask app."""
    app = Flask(__name__)
    app.config['TESTING'] = True

    @app.route('/protected')
    @require_auth
    def protected():
        return {'user_id': request.user_id}

    @app.route('/verify_protected')
    def verify_protected():
        result = verify_auth()
        if result is not None:
            return result
        return {'status': 'ok'}

    return app


class TestRequireAuth:
    """Tests for the @require_auth decorator."""

    def test_missing_auth_header(self, app):
        """Returns 401 when no Authorization header is present."""
        with app.test_client() as client:
            resp = client.get('/protected')
            assert resp.status_code == 401
            data = resp.get_json()
            assert data['success'] is False
            assert 'Authorization' in data['error']

    def test_invalid_auth_header_format(self, app):
        """Returns 401 when Authorization header is not Bearer."""
        with app.test_client() as client:
            resp = client.get('/protected', headers={'Authorization': 'Basic abc123'})
            assert resp.status_code == 401

    def test_supabase_not_configured(self, app):
        """Returns 500 when Supabase env vars are missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear cached state
            import app.auth as auth_module
            auth_module._supabase = None
            auth_module._supabase_error = None
            auth_module._supabase_error_time = 0

            with app.test_client() as client:
                resp = client.get('/protected', headers={'Authorization': 'Bearer test-token'})
                assert resp.status_code == 500
                data = resp.get_json()
                assert 'not configured' in data['error']

    def test_valid_token(self, app):
        """Returns 200 and sets request.user_id when token is valid."""
        mock_user = MagicMock()
        mock_user.user.id = 'user-123'
        mock_auth = MagicMock()
        mock_auth.get_user.return_value = mock_user
        mock_client = MagicMock()
        mock_client.auth = mock_auth

        with patch('app.auth._get_supabase_admin', return_value=(mock_client, None)):
            with app.test_client() as client:
                resp = client.get('/protected', headers={'Authorization': 'Bearer valid-token'})
                assert resp.status_code == 200
                data = resp.get_json()
                assert data['user_id'] == 'user-123'

    def test_invalid_token(self, app):
        """Returns 401 when Supabase rejects the token."""
        mock_client = MagicMock()
        mock_client.auth.get_user.side_effect = Exception('Invalid token')

        with patch('app.auth._get_supabase_admin', return_value=(mock_client, None)):
            with app.test_client() as client:
                resp = client.get('/protected', headers={'Authorization': 'Bearer bad-token'})
                assert resp.status_code == 401
                data = resp.get_json()
                assert 'Invalid token' in data['error']

    def test_supabase_unreachable(self, app):
        """Returns 503 when Supabase service is down."""
        with patch('app.auth._get_supabase_admin', return_value=(None, ('Supabase service unreachable', 503))):
            with app.test_client() as client:
                resp = client.get('/protected', headers={'Authorization': 'Bearer token'})
                assert resp.status_code == 503
                data = resp.get_json()
                assert 'unreachable' in data['error']


class TestVerifyAuth:
    """Tests for the verify_auth() standalone helper."""

    def test_returns_none_on_success(self, app):
        """verify_auth() returns None when auth is valid."""
        mock_user = MagicMock()
        mock_user.user.id = 'user-456'
        mock_auth = MagicMock()
        mock_auth.get_user.return_value = mock_user
        mock_client = MagicMock()
        mock_client.auth = mock_auth

        with patch('app.auth._get_supabase_admin', return_value=(mock_client, None)):
            with app.test_request_context('/verify_protected', headers={'Authorization': 'Bearer valid'}):
                result = verify_auth()
                assert result is None
                assert request.user_id == 'user-456'

    def test_returns_response_on_failure(self, app):
        """verify_auth() returns (response, status) when auth fails."""
        with app.test_request_context('/verify_protected'):
            result = verify_auth()
            assert result is not None
            response, status = result
            assert status == 401


class TestGetSupabaseAdmin:
    """Tests for the _get_supabase_admin() connection manager."""

    def setup_method(self):
        """Reset cached state before each test."""
        import app.auth as auth_module
        auth_module._supabase = None
        auth_module._supabase_error = None
        auth_module._supabase_error_time = 0

    def test_returns_error_when_env_vars_missing(self):
        """Returns (None, error_info) when SUPABASE_URL is not set."""
        with patch.dict(os.environ, {}, clear=True):
            client, err = _get_supabase_admin()
            assert client is None
            assert err is not None
            message, status = err
            assert status == 500
            assert 'not configured' in message

    def test_caches_successful_connection(self):
        """Caches the client after first successful connection."""
        import app.auth as auth_module

        mock_client = MagicMock()
        mock_client.auth.session = MagicMock()
        mock_client.auth.session.access_token = 'test'

        with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'key'}):
            with patch('app.auth.create_client', return_value=mock_client):
                client1, err1 = _get_supabase_admin()
                client2, err2 = _get_supabase_admin()

                assert err1 is None
                assert err2 is None
                assert client1 is client2  # Same cached instance

    def test_caches_failure_with_cooldown(self):
        """Caches failure and returns it within cooldown period."""
        import app.auth as auth_module

        with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'key'}):
            with patch('app.auth.create_client', side_effect=Exception('Connection refused')):
                client1, err1 = _get_supabase_admin()
                client2, err2 = _get_supabase_admin()

                assert client1 is None
                assert client2 is None
                assert err1 is not None
                _, status = err1
                assert status == 503

    def test_retries_after_cooldown(self):
        """Retries connection after cooldown period expires."""
        import app.auth as auth_module
        import time

        with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'key'}):
            with patch('app.auth.create_client', side_effect=Exception('Connection refused')):
                _get_supabase_admin()

                # Simulate cooldown expiry
                auth_module._supabase_error_time = time.time() - 60

                # Should retry (and fail again in this test)
                client, err = _get_supabase_admin()
                assert client is None
                assert err is not None
