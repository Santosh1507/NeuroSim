"""Supabase database layer for persistent storage."""

import os
from datetime import datetime
from typing import Dict, List, Optional

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
                print("Supabase connected.")
            except Exception as e:
                print(f"Supabase connection failed: {e}")
                self.client = None
                self.enabled = False
        else:
            self.client = None
            self.enabled = False
            if not SUPABASE_AVAILABLE:
                print("Supabase package not available. Using in-memory storage.")
            else:
                print("Supabase not configured. Using in-memory storage.")

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


db = Database()
