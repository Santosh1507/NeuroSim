"""Shared backend utilities used across multiple route modules.

Centralises helpers that were previously duplicated across upload.py,
predict.py, and analysis.py to avoid maintenance drift.
"""

from pathlib import Path
from typing import Optional


def is_video_magic(header: bytes) -> bool:
    """Check if the first bytes of a file match known video format signatures.

    Checks:
      - ftyp box (MP4, MOV, M4V, and variants): bytes 4-8 == b"ftyp"
        or byte 0-4 == b"ftyp" (some writers place it at the start)
      - AVI: bytes 0-4 == b"RIFF" and bytes 8-12 == b"AVI "
      - WebM/MKV: EBML magic bytes 0-4 == 0x1A45DFA3
    """
    if len(header) < 12:
        return False
    if header[4:8] == b"ftyp" or header[0:4] == b"ftyp":
        return True
    if header[0:4] == b"RIFF" and header[8:12] == b"AVI ":
        return True
    if len(header) >= 4 and header[0:4] == b"\x1a\x45\xdf\xa3":
        return True
    return False


def is_allowed_video_extension(filename: str) -> bool:
    """Return True if the file extension is in the supported set."""
    allowed = {".mp4", ".mov", ".avi", ".webm"}
    return Path(filename).suffix.lower() in allowed


def check_free_tier_limit(user_id: str, max_analyses: int) -> Optional[str]:
    """Return an error message string if the user has hit their free tier limit.

    Returns None if the user is within the limit or is premium/anonymous.
    Callers should raise HTTPException(403, ...) if this returns a non-None value.

    Import _usage_tracker and _is_premium lazily to avoid circular imports.
    """
    if user_id == "anonymous":
        return None
    from shared_state import _usage_tracker, _is_premium
    if _is_premium(user_id):
        return None
    current_usage = _usage_tracker.get(user_id, 0)
    if current_usage >= max_analyses:
        return (
            f"Free tier limit reached ({max_analyses}/month). "
            "Upgrade to Pro for unlimited analyses."
        )
    return None
