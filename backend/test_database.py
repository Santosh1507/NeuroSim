"""Tests for database module in fallback (no Supabase) mode."""

import pytest

# Import directly — Database() singleton is created at import time
# in fallback mode since no SUPABASE_URL is set in test env.
from database import Database, db


class TestDatabaseFallbackMode:
    """All tests run in fallback mode (no Supabase env vars)."""

    def test_db_is_fallback_mode(self):
        assert db.enabled is False
        assert db.client is None

    @pytest.mark.asyncio
    async def test_insert_video_returns_record(self):
        result = await db.insert_video("test-id", "test.mp4")
        assert result["id"] == "test-id"
        assert result["filename"] == "test.mp4"
        assert result["status"] == "uploaded"
        assert result["user_id"] == "anonymous"
        assert "upload_time" in result

    @pytest.mark.asyncio
    async def test_insert_video_custom_status_and_user(self):
        result = await db.insert_video("custom-id", "video.mov", status="processing", user_id="user-1")
        assert result["id"] == "custom-id"
        assert result["status"] == "processing"
        assert result["user_id"] == "user-1"

    @pytest.mark.asyncio
    async def test_get_video_returns_none_in_fallback(self):
        result = await db.get_video("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_video_status_does_not_crash(self):
        # Should not raise in fallback mode
        await db.update_video_status("test-id", "analyzed")

    @pytest.mark.asyncio
    async def test_list_videos_returns_empty_in_fallback(self):
        result = await db.list_videos()
        assert result == []

    @pytest.mark.asyncio
    async def test_insert_analysis_returns_record(self):
        analysis_data = {"hook_score": 85.0}
        result = await db.insert_analysis("test-id", analysis_data)
        assert result["id"] == "analysis_test-id"
        assert result["video_id"] == "test-id"
        assert result["data"] == analysis_data
        assert result["user_id"] == "anonymous"
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_insert_analysis_custom_user(self):
        result = await db.insert_analysis("vid-2", {"score": 90}, user_id="premium-user")
        assert result["user_id"] == "premium-user"

    @pytest.mark.asyncio
    async def test_get_analysis_returns_none_in_fallback(self):
        result = await db.get_analysis("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_independent_db_instance_fallback(self):
        """A fresh Database() instance should also detect fallback."""
        fresh = Database()
        assert fresh.enabled is False
        assert fresh.client is None

    @pytest.mark.asyncio
    async def test_insert_and_get_analysis_independent(self):
        """Arrange: insert via a fresh instance; Act+Assert: fallback mode never persists."""
        fresh = Database()
        await fresh.insert_analysis("orphan", {"score": 50})
        result = await fresh.get_analysis("orphan")
        assert result is None  # Fallback mode never persists — no crosstalk risk
