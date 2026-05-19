"""Tests for StorageAdapter — Supabase + in-memory cache unified layer."""
import pytest
import time
import asyncio
import storage_adapter
from storage_adapter import (
    StorageAdapter,
    _videos_cache,
    _analyses_cache,
    _cache_timestamps,
    _evict_stale,
)


@pytest.fixture
def store():
    """Fresh store with cleared caches for each test."""
    adapter = StorageAdapter()
    adapter._reset()
    yield adapter
    adapter._reset()


class TestInsertVideo:
    @pytest.mark.asyncio
    async def test_insert_video_returns_record(self, store):
        result = await store.insert_video("vid_1", "test.mp4", user_id="user_1")
        assert result["id"] == "vid_1"
        assert result["filename"] == "test.mp4"
        assert result["user_id"] == "user_1"
        assert result["status"] == "uploaded"

    @pytest.mark.asyncio
    async def test_insert_video_custom_status(self, store):
        result = await store.insert_video("vid_2", "test.mp4", status="processing")
        assert result["status"] == "processing"

    @pytest.mark.asyncio
    async def test_insert_video_populates_cache(self, store):
        await store.insert_video("vid_3", "test.mp4")
        assert "vid_3" in _videos_cache
        assert _videos_cache["vid_3"]["filename"] == "test.mp4"

    @pytest.mark.asyncio
    async def test_insert_video_touches_timestamp(self, store):
        await store.insert_video("vid_4", "test.mp4")
        assert "v:vid_4" in _cache_timestamps


class TestGetVideo:
    @pytest.mark.asyncio
    async def test_get_video_from_cache(self, store):
        await store.insert_video("vid_5", "test.mp4")
        result = await store.get_video("vid_5")
        assert result is not None
        assert result["id"] == "vid_5"

    @pytest.mark.asyncio
    async def test_get_video_not_found(self, store):
        result = await store.get_video("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_video_none_after_delete(self, store):
        await store.insert_video("vid_6", "test.mp4")
        await store.delete_video("vid_6")
        assert await store.get_video("vid_6") is None


class TestListVideos:
    @pytest.mark.asyncio
    async def test_list_videos_empty(self, store):
        assert await store.list_videos() == []

    @pytest.mark.asyncio
    async def test_list_videos_returns_all(self, store):
        await store.insert_video("v1", "a.mp4")
        await store.insert_video("v2", "b.mp4")
        await store.insert_video("v3", "c.mp4")
        assert len(await store.list_videos()) == 3

    @pytest.mark.asyncio
    async def test_list_videos_respects_limit(self, store):
        for i in range(10):
            await store.insert_video(f"v{i}", f"file{i}.mp4")
        assert len(await store.list_videos(limit=5)) == 5


class TestUpdateVideoStatus:
    @pytest.mark.asyncio
    async def test_update_status(self, store):
        await store.insert_video("vid_7", "test.mp4")
        await store.update_video_status("vid_7", "completed")
        result = await store.get_video("vid_7")
        assert result["status"] == "completed"


class TestDeleteVideo:
    @pytest.mark.asyncio
    async def test_delete_removes_from_cache(self, store):
        await store.insert_video("vid_8", "test.mp4")
        await store.delete_video("vid_8")
        assert "vid_8" not in _videos_cache

    @pytest.mark.asyncio
    async def test_delete_removes_timestamp(self, store):
        await store.insert_video("vid_9", "test.mp4")
        await store.delete_video("vid_9")
        assert "v:vid_9" not in _cache_timestamps


class TestInsertAnalysis:
    @pytest.mark.asyncio
    async def test_insert_analysis_returns_record(self, store):
        analysis = {"hook_score": 0.8, "viral_potential": 0.6}
        result = await store.insert_analysis("vid_10", analysis, user_id="user_1")
        assert result["hook_score"] == 0.8
        assert result["viral_potential"] == 0.6

    @pytest.mark.asyncio
    async def test_insert_analysis_populates_cache(self, store):
        await store.insert_analysis("vid_11", {"hook_score": 0.7})
        assert "vid_11" in _analyses_cache
        assert _analyses_cache["vid_11"]["hook_score"] == 0.7


class TestGetAnalysis:
    @pytest.mark.asyncio
    async def test_get_analysis_from_cache(self, store):
        await store.insert_analysis("vid_12", {"hook_score": 0.9})
        result = await store.get_analysis("vid_12")
        assert result is not None
        assert result["hook_score"] == 0.9

    @pytest.mark.asyncio
    async def test_get_analysis_not_found(self, store):
        assert await store.get_analysis("nonexistent") is None

    @pytest.mark.asyncio
    async def test_get_analysis_normalizes_supabase_wrapping(self, store):
        """Supabase stores {"data": {...}}, cache stores flat. get_analysis returns flat."""
        await store.insert_analysis("vid_13", {"hook_score": 0.5, "risk_score": 0.3})
        result = await store.get_analysis("vid_13")
        assert "data" not in result
        assert result["hook_score"] == 0.5


class TestDeleteAnalysis:
    @pytest.mark.asyncio
    async def test_delete_removes_from_cache(self, store):
        await store.insert_analysis("vid_14", {"score": 1.0})
        await store.delete_analysis("vid_14")
        assert "vid_14" not in _analyses_cache


class TestWarmup:
    @pytest.mark.asyncio
    async def test_warmup_returns_zero_without_supabase(self, store):
        assert await store.warmup(limit=5) == 0


class TestGetCachedVideoIds:
    @pytest.mark.asyncio
    async def test_get_cached_video_ids(self, store):
        await store.insert_video("vid_15", "test.mp4")
        assert "vid_15" in await store.get_cached_video_ids()


class TestGetAnalyticsSnapshot:
    @pytest.mark.asyncio
    async def test_snapshot_empty(self, store):
        s = await store.get_analytics_snapshot()
        assert s["total_analyses"] == 0
        assert s["total_videos"] == 0

    @pytest.mark.asyncio
    async def test_snapshot_with_data(self, store):
        await store.insert_video("vid_16", "test.mp4")
        await store.insert_analysis("vid_16", {"hook_score": 0.8, "viral_potential": 0.6})
        s = await store.get_analytics_snapshot()
        assert s["total_videos"] >= 1
        assert s["total_analyses"] >= 1


class TestCacheEviction:
    @pytest.mark.asyncio
    async def test_evict_removes_expired_videos(self, store):
        await store.insert_video("vid_17", "test.mp4")
        _cache_timestamps["v:vid_17"] = time.time() - 7200
        storage_adapter._last_eviction = 0
        _evict_stale()
        assert "vid_17" not in _videos_cache

    @pytest.mark.asyncio
    async def test_evict_keeps_fresh_videos(self, store):
        await store.insert_video("vid_18", "test.mp4")
        storage_adapter._last_eviction = 0
        _evict_stale()
        assert "vid_18" in _videos_cache

    @pytest.mark.asyncio
    async def test_evict_removes_expired_analyses(self, store):
        await store.insert_analysis("vid_19", {"score": 1.0})
        _cache_timestamps["a:vid_19"] = time.time() - 3600
        storage_adapter._last_eviction = 0
        _evict_stale()
        assert "vid_19" not in _analyses_cache
