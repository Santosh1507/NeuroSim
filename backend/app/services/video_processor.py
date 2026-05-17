"""
Video Processing Service
Handles video upload, frame extraction via FFmpeg, and transcription via Groq Whisper API.
"""

import os
import uuid
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import httpx

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.video_processor')

# Groq Whisper API endpoint
GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


class VideoProcessor:
    """Processes uploaded videos: extracts frames and transcribes audio."""

    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = Path(upload_dir or Config.UPLOAD_FOLDER) / 'neurosim'
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._ffmpeg_available: Optional[bool] = None

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available on the system."""
        if self._ffmpeg_available is not None:
            return self._ffmpeg_available
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True, text=True, timeout=10
            )
            self._ffmpeg_available = result.returncode == 0
        except Exception:
            self._ffmpeg_available = False
        return self._ffmpeg_available

    def process_video(self, video_path: str) -> Dict[str, Any]:
        """
        Process a single video file.

        Args:
            video_path: Path to the uploaded video file.

        Returns:
            Dict with frames_dir, transcript, duration, frame_count.
        """
        video_id = str(uuid.uuid4())[:8]
        work_dir = self.upload_dir / video_id
        work_dir.mkdir(parents=True, exist_ok=True)

        if not self._check_ffmpeg():
            logger.error("FFmpeg is not installed or not in PATH")
            return {
                'video_id': video_id,
                'frames_dir': None,
                'frame_count': 0,
                'duration_seconds': 0,
                'transcript': '',
                'processed_at': datetime.utcnow().isoformat(),
                'error': 'FFmpeg is not installed or not in PATH',
            }

        logger.info(f"Processing video: {video_path} -> {work_dir}")

        # Extract frames at 1fps
        frames_dir = work_dir / 'frames'
        frames_dir.mkdir(exist_ok=True)
        frame_count = self._extract_frames(video_path, frames_dir)

        # Get video duration
        duration = self._get_duration(video_path)

        # Extract audio and transcribe
        transcript = self._transcribe_video(video_path)

        result = {
            'video_id': video_id,
            'frames_dir': str(frames_dir),
            'frame_count': frame_count,
            'duration_seconds': duration,
            'transcript': transcript,
            'processed_at': datetime.utcnow().isoformat(),
        }

        logger.info(f"Video processing complete: {frame_count} frames, {duration}s, transcript length={len(transcript)}")
        return result

    def _extract_frames(self, video_path: str, frames_dir: Path) -> int:
        """Extract frames at 1fps using FFmpeg."""
        output_pattern = str(frames_dir / 'frame_%04d.jpg')
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', 'fps=1',
            '-q:v', '2',
            output_pattern,
            '-y',
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                logger.warning(f"FFmpeg stderr: {result.stderr[:500]}")

            # Count extracted frames
            frame_count = len(list(frames_dir.glob('*.jpg')))
            return frame_count

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg frame extraction timed out")
            return 0
        except Exception as e:
            logger.error(f"FFmpeg frame extraction failed: {e}")
            return 0

    def _get_duration(self, video_path: str) -> float:
        """Get video duration in seconds using ffprobe."""
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            duration = float(result.stdout.strip())
            return duration
        except Exception as e:
            logger.warning(f"Failed to get video duration: {e}")
            return 0.0

    def _transcribe_video(self, video_path: str) -> str:
        """
        Extract audio and transcribe using Groq Whisper API.
        Falls back to empty string if transcription fails.
        """
        groq_api_key = Config.GROQ_API_KEY
        if not groq_api_key:
            logger.warning("GROQ_API_KEY not configured, skipping transcription")
            return ""

        try:
            # Extract audio to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_audio:
                audio_path = tmp_audio.name

            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                audio_path,
                '-y',
            ]
            subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # Send to Groq Whisper API
            with open(audio_path, 'rb') as f:
                files = {'file': (os.path.basename(audio_path), f, 'audio/wav')}
                data = {
                    'model': 'whisper-large-v3-turbo',
                    'response_format': 'text',
                    'language': 'en',
                }
                headers = {
                    'Authorization': f'Bearer {groq_api_key}',
                }

                response = httpx.post(
                    GROQ_WHISPER_URL,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=120.0,
                )
                response.raise_for_status()
                transcript = response.text.strip()

            # Clean up temp audio file
            try:
                os.unlink(audio_path)
            except OSError:
                pass

            return transcript

        except httpx.HTTPStatusError as e:
            logger.error(f"Groq Whisper API error: {e.response.status_code} - {e.response.text[:200]}")
            return ""
        except subprocess.TimeoutExpired:
            logger.error("Audio extraction timed out")
            return ""
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
