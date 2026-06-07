"""Frame extraction from video using ffmpeg scene detection."""

from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import httpx

import shutil

FFMPEG_PATH = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
FFPROBE_PATH = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
DIRECT_VIDEO_HOSTS = ("snssdk.com", "douyinvod.com", "bytecdn.cn", "byteimg.com")


async def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds."""
    cmd = [
        FFPROBE_PATH,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        video_path,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    if proc.returncode != 0:
        return 0.0
    info = json.loads(stdout)
    return float(info.get("format", {}).get("duration", 0))


async def extract_keyframes(
    video_path: str,
    output_dir: str | None = None,
    max_frames: int = 50,
    scene_threshold: float = 0.3,
) -> list[dict[str, Any]]:
    """Extract keyframes using scene detection.

    Returns a list of dicts with: path, timestamp, base64 (if small enough).
    Uses ffmpeg's built-in scene change detection.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="ad_frames_")

    os.makedirs(output_dir, exist_ok=True)

    # ffmpeg scene detection: compares successive frames, outputs keyframes
    cmd = [
        FFMPEG_PATH,
        "-i", video_path,
        "-vf", f"select='gt(scene\\,{scene_threshold})',showinfo",
        "-vsync", "vfr",
        "-frame_pts", "1",
        "-q:v", "2",
        f"{output_dir}/frame_%04d.jpg",
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    timestamps = _parse_showinfo_timestamps(stderr.decode("utf-8", errors="ignore"))

    # Collect output frames
    frame_files = sorted(
        [f for f in os.listdir(output_dir) if f.endswith(".jpg") and f.startswith("frame_")],
        key=lambda x: int(x.replace("frame_", "").replace(".jpg", "")),
    )

    # Fallback: if scene detection finds nothing, use uniform sampling
    if not frame_files:
        frame_files = await _uniform_sample(video_path, output_dir, max_frames)
        timestamps = []

    if len(frame_files) > max_frames:
        step = len(frame_files) / max_frames
        indexes = [int(i * step) for i in range(max_frames)]
        frame_files = [frame_files[index] for index in indexes]
        if len(timestamps) >= max(indexes) + 1:
            timestamps = [timestamps[index] for index in indexes]
        frame_files = list(dict.fromkeys(frame_files))

    duration = await get_video_duration(video_path)
    frames = []
    num_frames = len(frame_files)
    for i, fname in enumerate(frame_files):
        filepath = os.path.join(output_dir, fname)
        timestamp = timestamps[i] if i < len(timestamps) else (i / max(num_frames, 1)) * duration

        frames.append({
            "path": filepath,
            "filename": fname,
            "timestamp": round(timestamp, 1),
            "width": 0,
            "height": 0,
        })

    return frames


def _parse_showinfo_timestamps(stderr: str) -> list[float]:
    return [float(value) for value in re.findall(r"pts_time:([0-9]+(?:\.[0-9]+)?)", stderr)]


async def _uniform_sample(
    video_path: str, output_dir: str, num_frames: int
) -> list[str]:
    """Fallback: extract frames at uniform intervals using ffmpeg."""
    cmd = [
        FFMPEG_PATH,
        "-i", video_path,
        "-vf", f"fps=1/{max(1, await _get_duration_seconds(video_path) / num_frames):.1f}",
        "-q:v", "2",
        "-frame_pts", "1",
        f"{output_dir}/frame_%04d.jpg",
        "-y",
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()
    return sorted(
        [f for f in os.listdir(output_dir) if f.endswith(".jpg") and f.startswith("frame_")],
        key=lambda x: int(x.replace("frame_", "").replace(".jpg", "")),
    )


async def _get_duration_seconds(video_path: str) -> float:
    """Quick duration check without full probe."""
    return await get_video_duration(video_path)


async def download_video(url: str, output_dir: str | None = None) -> str | None:
    """Download a video using yt-dlp. Returns the path to the downloaded file."""
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="ad_video_")

    if any(host in url for host in DIRECT_VIDEO_HOSTS):
        direct_path = await _download_direct_video(url, output_dir)
        if direct_path:
            return direct_path

    yt_dlp = str(Path(__file__).resolve().parent.parent / ".venv" / "bin" / "yt-dlp")

    cmd = [
        yt_dlp,
        url,
        "-o", f"{output_dir}/%(id)s.%(ext)s",
        "--no-playlist",
        "--no-check-certificates",
        "--socket-timeout", "30",
        "--retries", "2",
        "--max-filesize", "500M",
        "--format", "mp4/best[height<=1080]",
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120.0)

        if proc.returncode != 0:
            return None

        # Find the downloaded file
        for f in os.listdir(output_dir):
            if f.endswith(".mp4") or f.endswith(".webm") or f.endswith(".mkv"):
                return os.path.join(output_dir, f)
        return None
    except asyncio.TimeoutError:
        return None


async def _download_direct_video(url: str, output_dir: str) -> str | None:
    output_path = os.path.join(output_dir, "source.mp4")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        ),
        "Referer": "https://www.douyin.com/",
    }
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60),
            follow_redirects=True,
            headers=headers,
        ) as client:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    return None
                with open(output_path, "wb") as target:
                    async for chunk in response.aiter_bytes():
                        target.write(chunk)
        if os.path.getsize(output_path) < 1024:
            os.remove(output_path)
            return None
        return output_path
    except (httpx.HTTPError, OSError):
        return None
