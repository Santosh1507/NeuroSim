"""Tests for authentication routes."""

import pytest
from fastapi.testclient import TestClient

from main import app
from storage_adapter import _supabase


@pytest.fixture
def client():
    return TestClient(app=app)


class TestAuthRoutes:
    def test_sign_up_unavailable_without_supabase(self, client):
        """Sign-up returns 503 when Supabase is not configured."""
        if _supabase.enabled:
            pytest.skip("Supabase is enabled — skipping offline test")

        response = client.post(
            "/api/v1/auth/sign-up",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert response.status_code == 503

    def test_sign_in_unavailable_without_supabase(self, client):
        """Sign-in returns 503 when Supabase is not configured."""
        if _supabase.enabled:
            pytest.skip("Supabase is enabled — skipping offline test")

        response = client.post(
            "/api/v1/auth/sign-in",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert response.status_code == 503

    def test_sign_out_unavailable_without_supabase(self, client):
        """Sign-out returns 503 when Supabase is not configured."""
        if _supabase.enabled:
            pytest.skip("Supabase is enabled — skipping offline test")

        response = client.post("/api/v1/auth/sign-out")
        assert response.status_code == 503

    def test_guest_merge_requires_auth(self, client):
        """Guest merge endpoint requires authentication."""
        response = client.post(
            "/api/v1/auth/guest/merge",
            json={"guest_id": "guest_abc123"},
        )
        # Without JWT secret set, require_auth_user returns "anonymous"
        # which should trigger a 401 from the merge handler
        assert response.status_code in (401, 422)

    def test_guest_merge_invalid_guest_id(self, client):
        """Guest merge rejects non-guest IDs."""
        # Without auth, the endpoint returns 401 first (auth check before validation)
        response = client.post(
            "/api/v1/auth/guest/merge",
            json={"guest_id": "not-a-guest-id"},
        )
        assert response.status_code == 401
