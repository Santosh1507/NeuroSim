"""Tests for Stripe webhook handling."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


class TestStripeWebhookConfigured:
    @patch("main.settings.stripe_webhook_secret", "whsec_test")
    @patch("main.settings.stripe_secret_key", "sk_test")
    def test_checkout_completed_activates_premium(self):
        from main import app, _premium_users
        _premium_users.clear()
        mock_event = {"type": "checkout.session.completed", "data": {"object": {"metadata": {"user_id": "premium_user_1"}}}}
        with patch("stripe.Webhook.construct_event", return_value=mock_event):
            client = TestClient(app)
            resp = client.post("/api/stripe/webhook", content=b'{}', headers={"stripe-signature": "test_sig"})
            assert resp.status_code == 200
            assert "premium_user_1" in _premium_users

    @patch("main.settings.stripe_webhook_secret", "whsec_test")
    @patch("main.settings.stripe_secret_key", "sk_test")
    def test_subscription_deleted_deactivates_premium(self):
        from main import app, _premium_users
        _premium_users.clear()
        _premium_users.add("churned_user")
        mock_event = {"type": "customer.subscription.deleted", "data": {"object": {"metadata": {"user_id": "churned_user"}, "id": "sub_test"}}}
        with patch("stripe.Webhook.construct_event", return_value=mock_event):
            client = TestClient(app)
            resp = client.post("/api/stripe/webhook", content=b'{}', headers={"stripe-signature": "test_sig"})
            assert resp.status_code == 200
            assert "churned_user" not in _premium_users

    @patch("main.settings.stripe_webhook_secret", "whsec_test")
    def test_invalid_signature_returns_400(self):
        from main import app
        with patch("stripe.Webhook.construct_event", side_effect=ValueError):
            client = TestClient(app)
            resp = client.post("/api/stripe/webhook", content=b"invalid", headers={"stripe-signature": "bad"})
            assert resp.status_code == 400


class TestStripeWebhookNotConfigured:
    @patch("main.settings.stripe_webhook_secret", "")
    def test_returns_501_when_not_configured(self):
        from main import app
        client = TestClient(app)
        assert client.post("/api/stripe/webhook").status_code == 501
