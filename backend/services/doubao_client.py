"""Doubao Seed 2.0 Lite video understanding client — Volcano Engine ARK API."""

from __future__ import annotations

import asyncio
import base64
import os
import tempfile
from pathlib import Path
from typing import Any

import httpx

ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
ARK_API_KEY = os.getenv("ARK_API_KEY", "").strip()
VIDEO_MODEL = os.getenv("DOUBAO_VIDEO_MODEL", "doubao-seed-2-0-lite-260215").strip()
VIDEO_FPS = float(os.getenv("DOUBAO_VIDEO_FPS", "1.0"))


def is_available() -> bool:
    return bool(ARK_API_KEY)


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json",
    }


async def upload_video(file_path: str, fps: float = VIDEO_FPS) -> str | None:
    """Upload a video file to ARK via Files API, return file_id."""
    if not os.path.exists(file_path):
        return None

    filename = os.path.basename(file_path)
    url = f"{ARK_BASE_URL}/files"

    async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
        try:
            with open(file_path, "rb") as f:
                files = {"file": (filename, f, "video/mp4")}
                data = {
                    "purpose": "user_data",
                    "preprocess_configs[video][fps]": str(fps),
                    "preprocess_configs[video][model]": VIDEO_MODEL,
                }
                resp = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {ARK_API_KEY}"},
                    files=files,
                    data=data,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    file_id = result.get("id", "")
                    if file_id:
                        # Wait for processing to complete
                        await _wait_for_file(client, file_id)
                        return file_id
                return None
        except Exception:
            return None


async def _wait_for_file(client: httpx.AsyncClient, file_id: str, timeout: float = 120) -> bool:
    """Poll until file status is 'active'."""
    url = f"{ARK_BASE_URL}/files/{file_id}"
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        try:
            resp = await client.get(url, headers={"Authorization": f"Bearer {ARK_API_KEY}"})
            if resp.status_code == 200:
                status = resp.json().get("status", "")
                if status == "active":
                    return True
                if status == "failed":
                    return False
        except Exception:
            pass
        await asyncio.sleep(2)
    return False


def video_to_base64(file_path: str) -> str | None:
    """Encode a video file as base64 data URL."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        # Detect mime type
        ext = Path(file_path).suffix.lower()
        mime_map = {".mp4": "video/mp4", ".webm": "video/webm", ".mkv": "video/x-matroska"}
        mime = mime_map.get(ext, "video/mp4")
        return f"data:{mime};base64,{data}"
    except Exception:
        return None


async def analyze_video(
    video_path: str | None = None,
    video_url: str | None = None,
    file_id: str | None = None,
    prompt: str = "请详细描述这个视频的内容。",
    fps: float = VIDEO_FPS,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """Call Doubao to analyze a video. Returns parsed response dict.

    Precedence: file_id > video_url > video_path
    """
    if not is_available():
        return {"_error": "ARK_API_KEY not configured"}

    # Build video content block
    video_block = None
    if file_id:
        video_block = {"type": "input_file", "file_id": file_id}
    elif video_url:
        video_block = {
            "type": "video_url",
            "video_url": {"url": video_url, "fps": fps},
        }
    elif video_path:
        b64 = video_to_base64(video_path)
        if b64:
            video_block = {
                "type": "video_url",
                "video_url": {"url": b64, "fps": fps},
            }

    if video_block is None:
        return {"_error": "No video source provided"}

    messages = [
        {
            "role": "user",
            "content": [
                video_block,
                {"type": "text", "text": prompt},
            ],
        }
    ]

    body = {
        "model": VIDEO_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(180)) as client:
        try:
            resp = await client.post(
                f"{ARK_BASE_URL}/chat/completions",
                headers=_headers(),
                json=body,
            )
            if resp.status_code != 200:
                return {"_error": f"ARK HTTP {resp.status_code}: {resp.text[:300]}"}

            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"content": content}
        except httpx.TimeoutException:
            return {"_error": "ARK request timed out"}
        except Exception as exc:
            return {"_error": str(exc)}
