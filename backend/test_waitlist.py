"""Tests for Waitlist module."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from shared_state import _waitlist

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_waitlist():
    _waitlist.clear()
    yield
    _waitlist.clear()


class TestWaitlistRoutes:
    def test_waitlist_signup_success_simulated_email(self):
        payload = {
            "email": "innovator@neurosim.ai",
            "name": "Jane Doe"
        }
        
        response = client.post("/api/v1/waitlist", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Joined waitlist!"
        assert data["email"] == "innovator@neurosim.ai"
        assert data["queue_position"] == 1
        assert data["email_status"] == "simulated"
        
        # Verify stored in-memory
        assert len(_waitlist) == 1
        assert _waitlist[0]["email"] == "innovator@neurosim.ai"
        assert _waitlist[0]["queue_position"] == 1

    def test_waitlist_signup_duplicate_fails(self):
        payload = {
            "email": "duplicate@neurosim.ai"
        }
        
        # First signup
        response1 = client.post("/api/v1/waitlist", json=payload)
        assert response1.status_code == 200
        
        # Second signup
        response2 = client.post("/api/v1/waitlist", json=payload)
        assert response2.status_code == 409
        assert "already on the waitlist" in response2.json()["detail"]

    def test_waitlist_signup_invalid_email_fails(self):
        payload = {
            "email": "not-an-email"
        }
        response = client.post("/api/v1/waitlist", json=payload)
        assert response.status_code == 422  # Pydantic validation error

    def test_waitlist_queue_position_increments(self):
        # Signup 1
        resp1 = client.post("/api/v1/waitlist", json={"email": "first@neurosim.ai"})
        assert resp1.status_code == 200
        assert resp1.json()["queue_position"] == 1
        
        # Signup 2
        resp2 = client.post("/api/v1/waitlist", json={"email": "second@neurosim.ai"})
        assert resp2.status_code == 200
        assert resp2.json()["queue_position"] == 2
        
        # Signup 3
        resp3 = client.post("/api/v1/waitlist", json={"email": "third@neurosim.ai"})
        assert resp3.status_code == 200
        assert resp3.json()["queue_position"] == 3

    @patch("routes.waitlist._send_email_smtp")
    @patch("routes.waitlist.settings")
    def test_waitlist_signup_smtp_delivery(self, mock_settings, mock_send_email):
        # Configure mock settings to simulate configured SMTP
        mock_settings.email_host = "smtp.neurosim.ai"
        mock_settings.email_username = "waitlist@neurosim.ai"
        mock_settings.email_port = 587
        mock_settings.email_from = "NeuroSim Waitlist <waitlist@neurosim.ai>"
        mock_settings.email_from_address = "waitlist@neurosim.ai"
        
        mock_send_email.return_value = True
        
        payload = {
            "email": "smtp-test@neurosim.ai",
            "name": "Smtp Tester"
        }
        
        response = client.post("/api/v1/waitlist", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["email_status"] == "delivered"
        
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        assert args[0] == "smtp-test@neurosim.ai"
        assert "Welcome to the NeuroSim Waitlist!" in args[1]
        assert "Your Waitlist Position" in args[2]
        assert "#1" in args[2]

    @patch("routes.waitlist._send_email_smtp")
    @patch("routes.waitlist.settings")
    def test_waitlist_signup_smtp_failure(self, mock_settings, mock_send_email):
        mock_settings.email_host = "smtp.neurosim.ai"
        mock_settings.email_username = "waitlist@neurosim.ai"
        mock_send_email.return_value = False
        
        payload = {
            "email": "smtp-fail@neurosim.ai"
        }
        
        response = client.post("/api/v1/waitlist", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["email_status"] == "failed"
