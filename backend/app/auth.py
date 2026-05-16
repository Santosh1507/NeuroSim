"""
Supabase JWT Authentication Decorator
Verifies Bearer tokens from Supabase Auth on every protected route.
"""

import os
import time
from functools import wraps
from flask import request, jsonify
from supabase import create_client

_supabase = None
_supabase_error = None
_supabase_error_time = 0
_RETRY_COOLDOWN = 30  # seconds before retrying a failed connection


def _get_supabase_admin():
    """
    Returns (client, error_info) tuple.
    - (client, None) on success
    - (None, (message, status)) on failure
    Separates 'not configured' from 'unreachable'.
    """
    global _supabase, _supabase_error, _supabase_error_time

    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        return None, ('Supabase not configured on server', 500)

    # If we have a cached client, try to use it
    if _supabase is not None and _supabase_error is None:
        return _supabase, None

    # If we recently failed, return cached error without retrying
    if _supabase_error is not None:
        if time.time() - _supabase_error_time < _RETRY_COOLDOWN:
            return None, _supabase_error
        # Cooldown expired, clear and retry
        _supabase_error = None
        _supabase_error_time = 0

    try:
        _supabase = create_client(url, key)
        # Verify the connection works by calling a lightweight method
        _supabase.auth.get_user(_supabase.auth.session.access_token if hasattr(_supabase.auth, 'session') else 'ping')
        _supabase_error = None
        return _supabase, None
    except Exception as e:
        _supabase_error = (f'Supabase service unreachable: {str(e)}', 503)
        _supabase_error_time = time.time()
        return None, _supabase_error


def _auth_error_response(message, status):
    """Create a JSON error response from error info tuple."""
    return jsonify({'success': False, 'error': message}), status


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Missing or invalid Authorization header'}), 401

        token = auth_header[7:]
        sb, err = _get_supabase_admin()
        if err is not None:
            return _auth_error_response(*err)

        try:
            user = sb.auth.get_user(token)
            request.user_id = user.user.id
        except Exception as e:
            return jsonify({'success': False, 'error': f'Invalid token: {str(e)}'}), 401

        return f(*args, **kwargs)
    return decorated


def verify_auth():
    """
    Standalone auth check for use in before_request hooks.
    Returns None if auth is valid, or a (response, status) tuple if invalid.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Missing or invalid Authorization header'}), 401

    token = auth_header[7:]
    sb, err = _get_supabase_admin()
    if err is not None:
        return _auth_error_response(*err)

    try:
        user = sb.auth.get_user(token)
        request.user_id = user.user.id
    except Exception as e:
        return jsonify({'success': False, 'error': f'Invalid token: {str(e)}'}), 401

    return None
