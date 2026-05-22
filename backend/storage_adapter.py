"""Unified storage adapter wrapping Supabase + in-memory cache.

Provides a consistent interface for video and analysis storage,
normalizing the shape differences between Supabase (wraps data in {"data": ...})
and the in-memory cache (flat dicts). Always writes to Supabase when available
and uses in-memory cache as a fast read-through layer.
"""

import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import settings

logger = logging.getLogger(__name__)


# ─── In-memory storage ────────────────────────────────────
 
_videos_cache: Dict[str, dict] = {}
_analyses_cache: Dict[str, dict] = {}
_ab_tests_cache: Dict[str, dict] = {}
_social_simulations_cache: Dict[str, dict] = {}
_validations_cache: Dict[str, dict] = {}
_cache_timestamps: Dict[str, float] = {}
_VIDEO_TTL = 3600  # 1 hour
_ANALYSIS_TTL = 1800  # 30 minutes
_AB_TEST_TTL = 1800  # 30 minutes
_SOCIAL_SIMULATION_TTL = 1800  # 30 minutes
_VALIDATION_TTL = 3600  # 1 hour
_last_eviction: float = 0
_EVICTION_INTERVAL = 30  # seconds between housekeeping sweeps
 
 
def _touch_cache(key: str):
    _cache_timestamps[key] = time.time()
 
 
def _evict_stale():
    """Remove stale entries from all caches. Throttled to once every _EVICTION_INTERVAL."""
    global _last_eviction
    now = time.time()
    if now - _last_eviction < _EVICTION_INTERVAL:
        return
    _last_eviction = now
    stale_videos = [
        k
        for k in _cache_timestamps
        if k.startswith("v:") and now - _cache_timestamps[k] > _VIDEO_TTL
    ]
    stale_analyses = [
        k
        for k in _cache_timestamps
        if k.startswith("a:") and now - _cache_timestamps[k] > _ANALYSIS_TTL
    ]
    stale_ab_tests = [
        k
        for k in _cache_timestamps
        if k.startswith("ab:") and now - _cache_timestamps[k] > _AB_TEST_TTL
    ]
    stale_social_simulations = [
        k
        for k in _cache_timestamps
        if k.startswith("ss:") and now - _cache_timestamps[k] > _SOCIAL_SIMULATION_TTL
    ]
    stale_validations = [
        k
        for k in _cache_timestamps
        if k.startswith("ve:") and now - _cache_timestamps[k] > _VALIDATION_TTL
    ]
    for k in stale_videos:
        vid = k[2:]
        _videos_cache.pop(vid, None)
        _cache_timestamps.pop(k, None)
    for k in stale_analyses:
        aid = k[2:]
        _analyses_cache.pop(aid, None)
        _cache_timestamps.pop(k, None)
    for k in stale_ab_tests:
        abid = k[3:]
        _ab_tests_cache.pop(abid, None)
        _cache_timestamps.pop(k, None)
    for k in stale_social_simulations:
        ssid = k[3:]
        _social_simulations_cache.pop(ssid, None)
        _cache_timestamps.pop(k, None)
    for k in stale_validations:
        veid = k[3:]
        _validations_cache.pop(veid, None)
        _cache_timestamps.pop(k, None)


# ─── Supabase import (soft) ───────────────────────────────

try:
    from supabase import Client, create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


class SupabaseClient:
    """Thin wrapper around the Supabase client with soft-fail."""

    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        self.client: Any = None
        self.enabled = False

        if url and key and SUPABASE_AVAILABLE:
            try:
                self.client = create_client(url, key)
                self.enabled = True
                logger.info("StorageAdapter: Supabase connected.")
            except Exception as e:
                logger.error(f"StorageAdapter: Supabase connection failed: {e}")
        else:
            reason = "package unavailable" if not SUPABASE_AVAILABLE else "not configured"
            logger.warning(f"StorageAdapter: Supabase {reason}. Using in-memory only.")


# Singleton
_supabase = SupabaseClient()


class StorageAdapter:
    """Unified storage access layer.

    Provides async read/write/delete for videos and analyses, normalizing
    the shape differences between the Supabase storage and in-memory cache.
    The in-memory cache is always the primary read source for speed; Supabase
    is written to in parallel when available.
    """

    # ─── Videos ───────────────────────────────────────────

    async def insert_video(
        self, video_id: str, filename: str, status: str = "uploaded", user_id: str = "anonymous"
    ) -> Dict:
        """Insert a video record into both Supabase and in-memory cache."""
        _evict_stale()
        record = {
            "id": video_id,
            "user_id": user_id,
            "filename": filename,
            "status": status,
            "upload_time": datetime.now().isoformat(),
        }

        if _supabase.enabled:
            try:
                result = _supabase.client.table("videos").insert(record).execute()
                record = result.data[0] if result.data else record
            except Exception as e:
                logger.warning(f"Supabase insert_video failed: {e}")

        _videos_cache[video_id] = record
        _touch_cache(f"v:{video_id}")
        return record

    async def get_video(self, video_id: str) -> Optional[Dict]:
        """Get a video record — in-memory cache first, then Supabase."""
        cached = _videos_cache.get(video_id)
        if cached is not None:
            return cached

        if _supabase.enabled:
            try:
                result = _supabase.client.table("videos").select("*").eq("id", video_id).execute()
                if result.data:
                    rec = result.data[0]
                    _videos_cache[video_id] = rec
                    _touch_cache(f"v:{video_id}")
                    return rec
            except Exception as e:
                logger.warning(f"Supabase get_video failed: {e}")

        return None

    async def list_videos(self, limit: int = 50) -> List[Dict]:
        """List recent videos — Supabase if available, else in-memory."""
        if _supabase.enabled:
            try:
                result = (
                    _supabase.client.table("videos")
                    .select("*")
                    .order("upload_time", desc=True)
                    .limit(limit)
                    .execute()
                )
                # Update cache from Supabase
                for rec in result.data:
                    _videos_cache[rec["id"]] = rec
                    _touch_cache(f"v:{rec['id']}")
                return result.data
            except Exception as e:
                logger.warning(f"Supabase list_videos failed: {e}")

        return sorted(
            list(_videos_cache.values()),
            key=lambda v: v.get("upload_time", ""),
            reverse=True,
        )[:limit]

    async def update_video_status(self, video_id: str, status: str) -> None:
        """Update video status in both stores."""
        _evict_stale()
        if video_id in _videos_cache:
            _videos_cache[video_id]["status"] = status
            _touch_cache(f"v:{video_id}")

        if _supabase.enabled:
            try:
                _supabase.client.table("videos").update({"status": status}).eq("id", video_id).execute()
            except Exception as e:
                logger.warning(f"Supabase update_video_status failed: {e}")

    async def delete_video(self, video_id: str) -> None:
        """Delete a video record from both stores."""
        _evict_stale()
        _videos_cache.pop(video_id, None)
        _cache_timestamps.pop(f"v:{video_id}", None)

        if _supabase.enabled:
            try:
                _supabase.client.table("videos").delete().eq("id", video_id).execute()
            except Exception as e:
                logger.warning(f"Supabase delete_video failed: {e}")

    # ─── Analyses ─────────────────────────────────────────

    async def insert_analysis(
        self, video_id: str, analysis: Dict, user_id: str = "anonymous"
    ) -> Dict:
        """Insert or update an analysis record into both stores.

        Uses upsert (on_conflict=video_id) so re-analyzing the same video
        overwrites the existing record without a unique constraint violation.
        The in-memory cache stores the analysis dict flat (as returned by the API).
        Supabase wraps it in {"data": analysis} — the adapter normalizes reads.
        """
        _evict_stale()
        if _supabase.enabled:
            try:
                record = {
                    "id": f"analysis_{video_id}",
                    "video_id": video_id,
                    "user_id": user_id,
                    "data": analysis,
                    "created_at": datetime.now().isoformat(),
                }
                # upsert: update if video_id already exists, insert if not
                _supabase.client.table("analyses").upsert(
                    record, on_conflict="video_id"
                ).execute()
            except Exception as e:
                logger.warning(f"Supabase insert_analysis failed: {e}")

        # Cache stores the flat analysis object
        _analyses_cache[video_id] = analysis
        _touch_cache(f"a:{video_id}")
        return analysis

    async def get_analysis(self, video_id: str) -> Optional[Dict]:
        """Get an analysis — in-memory cache first, then Supabase (normalized)."""
        cached = _analyses_cache.get(video_id)
        if cached is not None:
            return cached

        if _supabase.enabled:
            try:
                result = (
                    _supabase.client.table("analyses")
                    .select("*")
                    .eq("video_id", video_id)
                    .execute()
                )
                if result.data:
                    # Normalize: unwrap Supabase's {"data": analysis} wrapping
                    analysis = result.data[0].get("data", result.data[0])
                    if isinstance(analysis, dict):
                        _analyses_cache[video_id] = analysis
                        _touch_cache(f"a:{video_id}")
                        return analysis
            except Exception as e:
                logger.warning(f"Supabase get_analysis failed: {e}")

        return None

    async def delete_analysis(self, video_id: str) -> None:
        """Delete an analysis record from both stores."""
        _evict_stale()
        _analyses_cache.pop(video_id, None)
        _cache_timestamps.pop(f"a:{video_id}", None)

        if _supabase.enabled:
            try:
                _supabase.client.table("analyses").delete().eq("video_id", video_id).execute()
            except Exception as e:
                logger.warning(f"Supabase delete_analysis failed: {e}")

    # ─── Bulk / Warmup ────────────────────────────────────

    async def warmup(self, limit: int = 20) -> int:
        """Pre-load recent analyses from Supabase into the in-memory cache.

        Returns the number of analyses loaded.
        Returns 0 if Supabase is not available.
        """
        _evict_stale()
        if not _supabase.enabled:
            return 0

        try:
            result = (
                _supabase.client.table("analyses")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            count = 0
            for row in result.data:
                video_id = row.get("video_id")
                analysis = row.get("data", row)
                if isinstance(analysis, dict) and video_id:
                    _analyses_cache[video_id] = analysis
                    _touch_cache(f"a:{video_id}")
                    count += 1
            logger.info(f"StorageAdapter: Warmed {count} analyses into cache")
            return count
        except Exception as e:
            logger.warning(f"StorageAdapter warmup failed: {e}")
            return 0

    async def get_cached_video_ids(self) -> List[str]:
        """Return all video IDs currently in either cache or Supabase."""
        ids = set(_videos_cache.keys())
        if _supabase.enabled:
            try:
                result = _supabase.client.table("videos").select("id").limit(1000).execute()
                ids.update(r["id"] for r in result.data)
            except Exception:
                pass
        return list(ids)

    async def get_analytics_snapshot(self) -> Dict:
        """Return aggregate analytics from the in-memory cache only (fast path)."""
        total = len(_analyses_cache)
        scores = []
        hooks = []
        virals = []
        for a in _analyses_cache.values():
            if isinstance(a, dict):
                scores.append(a.get("success_probability", 0))
                hooks.append(a.get("hook_score", 0))
                virals.append(a.get("viral_potential", 0))
        return {
            "total_analyses": total,
            "total_videos": len(_videos_cache),
            "average_success_probability": round(sum(scores) / len(scores), 1) if scores else 0,
            "average_hook_score": round(sum(hooks) / len(hooks), 1) if hooks else 0,
            "average_viral_potential": round(sum(virals) / len(virals), 1) if virals else 0,
        }

    # ─── A/B Tests ─────────────────────────────────────────

    async def insert_ab_test(
        self,
        ab_test_id: str,
        name: str,
        baseline_video_id: str,
        variant_video_id: Optional[str],
        variant_script: Optional[str],
        results: Dict,
        user_id: str = "anonymous",
    ) -> Dict:
        """Insert an A/B test record into both Supabase and in-memory cache."""
        _evict_stale()
        record = {
            "id": ab_test_id,
            "user_id": user_id,
            "name": name,
            "baseline_video_id": baseline_video_id,
            "variant_video_id": variant_video_id,
            "variant_script": variant_script,
            "results": results,
            "created_at": datetime.now().isoformat(),
        }

        if _supabase.enabled:
            try:
                result = _supabase.client.table("ab_tests").insert(record).execute()
                record = result.data[0] if result.data else record
            except Exception as e:
                logger.warning(f"Supabase insert_ab_test failed: {e}")

        _ab_tests_cache[ab_test_id] = record
        _touch_cache(f"ab:{ab_test_id}")
        return record

    async def get_ab_test(self, ab_test_id: str) -> Optional[Dict]:
        """Get an A/B test — in-memory cache first, then Supabase."""
        cached = _ab_tests_cache.get(ab_test_id)
        if cached is not None:
            return cached

        if _supabase.enabled:
            try:
                result = _supabase.client.table("ab_tests").select("*").eq("id", ab_test_id).execute()
                if result.data:
                    rec = result.data[0]
                    _ab_tests_cache[ab_test_id] = rec
                    _touch_cache(f"ab:{ab_test_id}")
                    return rec
            except Exception as e:
                logger.warning(f"Supabase get_ab_test failed: {e}")

        return None

    async def list_ab_tests(self, user_id: str = "anonymous", limit: int = 50) -> List[Dict]:
        """List historical A/B tests — Supabase if available, else in-memory."""
        if _supabase.enabled:
            try:
                result = (
                    _supabase.client.table("ab_tests")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute()
                )
                for rec in result.data:
                    _ab_tests_cache[rec["id"]] = rec
                    _touch_cache(f"ab:{rec['id']}")
                return result.data
            except Exception as e:
                logger.warning(f"Supabase list_ab_tests failed: {e}")

        return sorted(
            [v for v in _ab_tests_cache.values() if v.get("user_id") == user_id],
            key=lambda v: v.get("created_at", ""),
            reverse=True,
        )[:limit]

    async def delete_ab_test(self, ab_test_id: str) -> None:
        """Delete an A/B test record from both stores."""
        _evict_stale()
        _ab_tests_cache.pop(ab_test_id, None)
        _cache_timestamps.pop(f"ab:{ab_test_id}", None)

        if _supabase.enabled:
            try:
                _supabase.client.table("ab_tests").delete().eq("id", ab_test_id).execute()
            except Exception as e:
                logger.warning(f"Supabase delete_ab_test failed: {e}")

    # ─── Social Simulations ────────────────────────────────

    async def insert_social_simulation(
        self,
        sim_id: str,
        video_id: str,
        platform: str,
        algorithmic_score: float,
        vtr: float,
        retention_data: Dict,
        user_id: str = "anonymous",
    ) -> Dict:
        """Insert a social simulation record into both Supabase and in-memory cache."""
        _evict_stale()
        record = {
            "id": sim_id,
            "user_id": user_id,
            "video_id": video_id,
            "platform": platform,
            "algorithmic_score": algorithmic_score,
            "vtr": vtr,
            "retention_data": retention_data,
            "created_at": datetime.now().isoformat(),
        }

        if _supabase.enabled:
            try:
                result = _supabase.client.table("social_simulations").insert(record).execute()
                record = result.data[0] if result.data else record
            except Exception as e:
                logger.warning(f"Supabase insert_social_simulation failed: {e}")

        _social_simulations_cache[sim_id] = record
        _touch_cache(f"ss:{sim_id}")
        return record

    async def get_social_simulation(self, sim_id: str) -> Optional[Dict]:
        """Get a social simulation — in-memory cache first, then Supabase."""
        cached = _social_simulations_cache.get(sim_id)
        if cached is not None:
            return cached

        if _supabase.enabled:
            try:
                result = _supabase.client.table("social_simulations").select("*").eq("id", sim_id).execute()
                if result.data:
                    rec = result.data[0]
                    _social_simulations_cache[sim_id] = rec
                    _touch_cache(f"ss:{sim_id}")
                    return rec
            except Exception as e:
                logger.warning(f"Supabase get_social_simulation failed: {e}")

        return None

    async def list_social_simulations(self, user_id: str = "anonymous", limit: int = 50) -> List[Dict]:
        """List historical social simulations — Supabase if available, else in-memory."""
        if _supabase.enabled:
            try:
                result = (
                    _supabase.client.table("social_simulations")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute()
                )
                for rec in result.data:
                    _social_simulations_cache[rec["id"]] = rec
                    _touch_cache(f"ss:{rec['id']}")
                return result.data
            except Exception as e:
                logger.warning(f"Supabase list_social_simulations failed: {e}")

        return sorted(
            [v for v in _social_simulations_cache.values() if v.get("user_id") == user_id],
            key=lambda v: v.get("created_at", ""),
            reverse=True,
        )[:limit]

    async def delete_social_simulation(self, sim_id: str) -> None:
        """Delete a social simulation record from both stores."""
        _evict_stale()
        _social_simulations_cache.pop(sim_id, None)
        _cache_timestamps.pop(f"ss:{sim_id}", None)

        if _supabase.enabled:
            try:
                _supabase.client.table("social_simulations").delete().eq("id", sim_id).execute()
            except Exception as e:
                logger.warning(f"Supabase delete_social_simulation failed: {e}")

    # ─── Validation Entries ────────────────────────────────

    async def insert_validation_entry(self, entry: Dict) -> Dict:
        """Insert a validation entry into both Supabase and in-memory cache."""
        _evict_stale()
        entry_id = entry.get("id", entry.get("video_id", uuid.uuid4().hex))
        record = {**entry, "id": entry_id}

        if _supabase.enabled:
            try:
                result = _supabase.client.table("validation_entries").insert(record).execute()
                record = result.data[0] if result.data else record
            except Exception as e:
                logger.warning(f"Supabase insert_validation_entry failed: {e}")

        _validations_cache[entry_id] = record
        _touch_cache(f"ve:{entry_id}")
        return record

    async def list_validation_entries(self, limit: int = 1000) -> List[Dict]:
        """List validation entries — Supabase if available, else in-memory cache."""
        if _supabase.enabled:
            try:
                result = (
                    _supabase.client.table("validation_entries")
                    .select("*")
                    .order("submitted_at", desc=True)
                    .limit(limit)
                    .execute()
                )
                for rec in result.data:
                    _validations_cache[rec["id"]] = rec
                    _touch_cache(f"ve:{rec['id']}")
                return result.data
            except Exception as e:
                logger.warning(f"Supabase list_validation_entries failed: {e}")

        return sorted(
            list(_validations_cache.values()),
            key=lambda v: v.get("submitted_at", ""),
            reverse=True,
        )[:limit]

    async def delete_validation_entry(self, entry_id: str) -> None:
        """Delete a validation entry from both stores."""
        _evict_stale()
        _validations_cache.pop(entry_id, None)
        _cache_timestamps.pop(f"ve:{entry_id}", None)

        if _supabase.enabled:
            try:
                _supabase.client.table("validation_entries").delete().eq("id", entry_id).execute()
            except Exception as e:
                logger.warning(f"Supabase delete_validation_entry failed: {e}")

    def _reset(self) -> None:
        """Clear all caches and timestamps. For testing only."""
        _videos_cache.clear()
        _analyses_cache.clear()
        _ab_tests_cache.clear()
        _social_simulations_cache.clear()
        _validations_cache.clear()
        _cache_timestamps.clear()


# Module-level singleton
store = StorageAdapter()
