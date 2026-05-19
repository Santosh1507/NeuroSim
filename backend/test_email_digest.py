"""Tests for email digest functionality."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestDigestSubscribe:
    def test_subscribe_new_email(self):
        """Subscribe to digest returns success."""
        from main import app, _digest_subs
        _digest_subs.clear()

        client = TestClient(app)
        response = client.post(
            "/api/digest/subscribe",
            json={"email": "test@example.com", "frequency": "weekly"},
            headers={"authorization": "Bearer dummy"},
        )
        assert response.status_code == 200
        assert "test@example.com" in _digest_subs

    def test_subscribe_duplicate_returns_409(self):
        """Duplicate subscription returns 409."""
        from main import app, _digest_subs
        _digest_subs.clear()
        _digest_subs["dup@example.com"] = {"frequency": "weekly"}

        client = TestClient(app)
        response = client.post(
            "/api/digest/subscribe",
            json={"email": "dup@example.com", "frequency": "weekly"},
            headers={"authorization": "Bearer dummy"},
        )
        assert response.status_code == 409


class TestDigestPreview:
    def test_preview_returns_stats(self):
        """Preview returns aggregated stats."""
        from main import app
        client = TestClient(app)
        response = client.get("/api/digest/preview")
        assert response.status_code == 200
        data = response.json()
        assert "total_analyses" in data


class TestSendEmailSmtp:
    @patch("main.settings.email_host", "smtp.example.com")
    @patch("main.settings.email_username", "user")
    @patch("main.settings.email_password", "pass")
    def test_smtp_not_reachable_returns_false(self):
        """SMTP send returns False when server is unreachable (graceful)."""
        from main import _send_email_smtp
        result = _send_email_smtp("test@example.com", "Test", "<p>Test</p>")
        assert result is False  # Graceful failure, no exception
