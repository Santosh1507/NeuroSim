"""YouTube Data API v3 client — video metadata and transcript fetching.

Quota: 10K units/day (~200 video lookups at 3 units each for snippet+contentDetails+statistics).
Transcript extraction uses youtube-transcript-api (no quota cost).
"""
import re
from typing import Any, Dict, Optional

import httpx
from config import settings


def extract_video_id(url_or_id: str) -> Optional[str]:
    """Extract YouTube video ID from URL or return as-is if already an ID."""
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
        return url_or_id

    patterns = [
        r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/live/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None


async def fetch_video_metadata(video_id: str) -> Dict[str, Any]:
    """Fetch video metadata from YouTube Data API v3.

    Costs ~3 units per call (snippet + contentDetails + statistics).
    Falls back gracefully if API key is not configured.
    """
    api_key = settings.youtube_api_key
    if not api_key:
        return {
            "video_id": video_id,
            "title": f"YouTube Video ({video_id[:8]}...)",
            "source": "youtube",
            "fallback": True,
            "note": "YouTube API key not configured",
        }

    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,contentDetails,statistics",
        "id": video_id,
        "key": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        return {
            "video_id": video_id,
            "title": f"YouTube Video ({video_id[:8]}...)",
            "source": "youtube",
            "fallback": True,
            "error": str(e),
        }

    if not data.get("items"):
        return {
            "video_id": video_id,
            "title": "Video not found",
            "source": "youtube",
            "error": "Video not found or is private",
        }

    item = data["items"][0]
    snippet = item.get("snippet", {})
    content_details = item.get("contentDetails", {})
    statistics = item.get("statistics", {})

    return {
        "video_id": video_id,
        "title": snippet.get("title", ""),
        "description": snippet.get("description", "")[:500],
        "channel": snippet.get("channelTitle", ""),
        "published_at": snippet.get("publishedAt", ""),
        "duration": content_details.get("duration", ""),
        "view_count": int(statistics.get("viewCount", 0)),
        "like_count": int(statistics.get("likeCount", 0)),
        "comment_count": int(statistics.get("commentCount", 0)),
        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        "source": "youtube",
        "fallback": False,
    }


async def fetch_youtube_transcript(video_id: str) -> Optional[str]:
    """Fetch transcript/captions from a YouTube video.

    Uses youtube-transcript-api. No API quota cost.
    Returns plain text transcript or None if unavailable.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=["en", "en-US", "en-GB"],
        )
        text = " ".join(entry["text"] for entry in transcript_list)
        return text.strip() if text.strip() else None
    except ImportError:
        return None
    except Exception:
        return None
