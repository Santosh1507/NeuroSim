"""Supabase database layer for persistent storage."""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from supabase import Client, create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


class Database:
    """Supabase-backed persistent storage."""

    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if url and key and SUPABASE_AVAILABLE:
            try:
                self.client = create_client(url, key)
                self.enabled = True
                logger.info("Supabase connected.")
            except Exception as e:
                logger.error(f"Supabase connection failed: {e}")
                self.client = None
                self.enabled = False
        else:
            self.client = None
            self.enabled = False
            if not SUPABASE_AVAILABLE:
                logger.warning("Supabase package not available. Using in-memory storage.")
            else:
                logger.warning("Supabase not configured. Using in-memory storage.")

    async def insert_video(
        self, video_id: str, filename: str, status: str = "uploaded", user_id: str = "anonymous"
    ) -> Dict:
        """Insert a video record."""
        record = {
            "id": video_id,
            "user_id": user_id,
            "filename": filename,
            "status": status,
            "upload_time": datetime.now().isoformat(),
        }

        if self.enabled:
            result = self.client.table("videos").insert(record).execute()
            return result.data[0] if result.data else record
        return record

    async def update_video_status(self, video_id: str, status: str) -> None:
        """Update video status."""
        if self.enabled:
            self.client.table("videos").update({"status": status}).eq("id", video_id).execute()

    async def get_video(self, video_id: str) -> Optional[Dict]:
        """Get a video record."""
        if self.enabled:
            result = self.client.table("videos").select("*").eq("id", video_id).execute()
            return result.data[0] if result.data else None
        return None

    async def list_videos(self, limit: int = 50) -> List[Dict]:
        """List recent videos."""
        if self.enabled:
            result = (
                self.client.table("videos")
                .select("*")
                .order("upload_time", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data
        return []

    async def insert_analysis(
        self, video_id: str, analysis: Dict, user_id: str = "anonymous"
    ) -> Dict:
        """Insert an analysis record."""
        record = {
            "id": f"analysis_{video_id}",
            "video_id": video_id,
            "user_id": user_id,
            "data": analysis,
            "created_at": datetime.now().isoformat(),
        }

        if self.enabled:
            result = self.client.table("analyses").insert(record).execute()
            return result.data[0] if result.data else record
        return record

    async def get_analysis(self, video_id: str) -> Optional[Dict]:
        """Get an analysis record."""
        if self.enabled:
            result = self.client.table("analyses").select("*").eq("video_id", video_id).execute()
            return result.data[0] if result.data else None
        return None

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
        """Insert an A/B test record."""
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

        if self.enabled:
            result = self.client.table("ab_tests").insert(record).execute()
            return result.data[0] if result.data else record
        return record

    async def get_ab_test(self, ab_test_id: str) -> Optional[Dict]:
        """Get an A/B test record."""
        if self.enabled:
            result = self.client.table("ab_tests").select("*").eq("id", ab_test_id).execute()
            return result.data[0] if result.data else None
        return None

    async def list_ab_tests(self, user_id: str = "anonymous", limit: int = 50) -> List[Dict]:
        """List historical A/B tests for a user."""
        if self.enabled:
            result = (
                self.client.table("ab_tests")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data
        return []

    async def delete_ab_test(self, ab_test_id: str) -> None:
        """Delete an A/B test record."""
        if self.enabled:
            self.client.table("ab_tests").delete().eq("id", ab_test_id).execute()

    async def insert_waitlist(self, email: str) -> Dict:
        """Insert email into waitlist and return the record with queue position."""
        if self.enabled:
            count = await self.get_waitlist_count()
            queue_pos = count + 1
            record = {
                "email": email,
                "queue_position": queue_pos,
                "created_at": datetime.now().isoformat(),
            }
            result = self.client.table("waitlist").insert(record).execute()
            return result.data[0] if result.data else record
        else:
            from shared_state import _waitlist
            for entry in _waitlist:
                if entry["email"] == email:
                    raise ValueError("You're already on the waitlist!")
            record = {
                "id": len(_waitlist) + 1,
                "email": email,
                "queue_position": len(_waitlist) + 1,
                "created_at": datetime.now().isoformat(),
            }
            _waitlist.append(record)
            return record

    async def get_waitlist_count(self) -> int:
        """Get total waitlist count."""
        if self.enabled:
            result = self.client.table("waitlist").select("id", count="exact").execute()
            return result.count if result.count is not None else 0
        else:
            from shared_state import _waitlist
            return len(_waitlist)

    async def is_waitlist_email_registered(self, email: str) -> bool:
        """Check if email is already in the waitlist."""
        if self.enabled:
            result = self.client.table("waitlist").select("id").eq("email", email).execute()
            return len(result.data) > 0
        else:
            from shared_state import _waitlist
            return any(entry["email"] == email for entry in _waitlist)

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
        """Insert a social simulation record."""
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

        if self.enabled:
            result = self.client.table("social_simulations").insert(record).execute()
            return result.data[0] if result.data else record
        return record

    async def get_social_simulation(self, sim_id: str) -> Optional[Dict]:
        """Get a social simulation record."""
        if self.enabled:
            result = self.client.table("social_simulations").select("*").eq("id", sim_id).execute()
            return result.data[0] if result.data else None
        return None

    async def list_social_simulations(self, user_id: str = "anonymous", limit: int = 50) -> List[Dict]:
        """List historical social simulations for a user."""
        if self.enabled:
            result = (
                self.client.table("social_simulations")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data
        return []

    async def delete_social_simulation(self, sim_id: str) -> None:
        """Delete a social simulation record."""
        if self.enabled:
            self.client.table("social_simulations").delete().eq("id", sim_id).execute()


db = Database()

