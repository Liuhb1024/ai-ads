"""Unified media understanding pipeline — ties frame extraction + transcription."""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Ensure the services directory is importable
_PARENT = Path(__file__).resolve().parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from frame_extractor import download_video, extract_keyframes  # noqa: E402
from ocr import frames_metadata, frames_to_base64_list  # noqa: E402
from transcriber import transcribe_video  # noqa: E402


@dataclass
class MediaAnalysis:
    url: str
    video_path: str = ""
    duration: float = 0.0
    transcript: str = ""
    transcript_segments: list[dict] = field(default_factory=list)
    transcript_language: str = ""
    frames: list[dict] = field(default_factory=list)
    frame_base64: list[dict] = field(default_factory=list)
    error: str = ""


async def analyze_video(url_or_path: str, max_frames: int = 30) -> MediaAnalysis:
    """Full media analysis pipeline for a video URL or local file."""

    result = MediaAnalysis(url=url_or_path)
    tmp_dir = tempfile.mkdtemp(prefix="ad_media_")

    try:
        # Step 1: Get video file
        if os.path.exists(url_or_path):
            video_path = url_or_path
            result.video_path = video_path
        else:
            video_path = await download_video(url_or_path, tmp_dir)
            if not video_path:
                result.error = "视频下载失败"
                return result
            result.video_path = video_path

        # Step 2: Extract keyframes
        frames_dir = os.path.join(tmp_dir, "frames")
        frames = await extract_keyframes(video_path, output_dir=frames_dir, max_frames=max_frames)
        frames = frames_metadata(frames)
        result.frames = frames

        # Step 3: Transcribe audio
        try:
            transcript_data = await transcribe_video(video_path)
            result.transcript = transcript_data["full_text"]
            result.transcript_segments = transcript_data["segments"]
            result.transcript_language = transcript_data["language"]
            result.duration = transcript_data["duration"]
        except Exception as exc:
            result.transcript = f"[转录失败: {exc}]"

        # Step 4: Generate base64 frame previews (up to 8 for API)
        result.frame_base64 = frames_to_base64_list(frames, max_frames=8)

    except Exception as exc:
        result.error = str(exc)

    return result
