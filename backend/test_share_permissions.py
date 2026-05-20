"""Tests for share link permissions."""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


class TestSharePermissions:
    def test_create_with_defaults(self):
        from main import app
        from shared_state import _share_links, _share_permissions
        _share_links.clear()
        _share_permissions.clear()
        client = TestClient(app)
        with patch("routes.share.store.get_analysis", new=AsyncMock(return_value={"id": "vid_test"})):
            resp = client.post("/api/v1/share", json={"video_id": "vid_test"}, headers={"authorization": "Bearer dummy"})
        assert resp.status_code == 200
        data = resp.json()
        assert "share_id" in data
        assert data["allow_download"] is True
        assert data["allow_embed"] is False

    def test_create_with_custom_permissions(self):
        from main import app
        from shared_state import _share_links, _share_permissions
        _share_links.clear()
        _share_permissions.clear()
        client = TestClient(app)
        with patch("routes.share.store.get_analysis", new=AsyncMock(return_value={"id": "vid_test"})):
            resp = client.post("/api/v1/share", json={
                "video_id": "vid_test",
                "allow_download": False,
                "allow_embed": True,
                "expires_in_days": 14,
            }, headers={"authorization": "Bearer dummy"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["allow_download"] is False
        assert data["allow_embed"] is True

    def test_permissions_stored_in_dict(self):
        from main import app
        from shared_state import _share_links, _share_permissions
        _share_links.clear()
        _share_permissions.clear()
        client = TestClient(app)
        with patch("routes.share.store.get_analysis", new=AsyncMock(return_value={"id": "vid_test"})):
            resp = client.post("/api/v1/share", json={
                "video_id": "vid_test",
                "allow_download": False,
            }, headers={"authorization": "Bearer dummy"})
        data = resp.json()
        share_id = data["share_id"]
        assert share_id in _share_permissions
        assert _share_permissions[share_id]["allow_download"] is False
        assert _share_permissions[share_id]["allow_embed"] is False
        assert _share_permissions[share_id]["expires_in_days"] == 7

    def test_404_when_analysis_missing(self):
        from main import app
        from shared_state import _share_links, _share_permissions
        _share_links.clear()
        _share_permissions.clear()
        client = TestClient(app)
        with patch("routes.share.store.get_analysis", new=AsyncMock(return_value=None)):
            resp = client.post("/api/v1/share", json={"video_id": "vid_missing"}, headers={"authorization": "Bearer dummy"})
        assert resp.status_code == 404
