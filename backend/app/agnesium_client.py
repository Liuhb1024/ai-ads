"""Agnes AI multimodal API client — text, image, and video generation.

OpenAI-compatible endpoints at https://apihub.agnes-ai.com/v1.
All models are free as of 2026-06-01.
"""

from __future__ import annotations

import asyncio
import json
import os
import base64 as b64
from io import BytesIO
from typing import Any

import httpx


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


AGNES_API_KEY = _env("AGNES_API_KEY")
AGNES_API_BASE = _env("AGNES_API_BASE", "https://apihub.agnes-ai.com/v1")

TEXT_MODEL = _env("AGNES_TEXT_MODEL", "agnes-2.0-flash")
IMAGE_MODEL = _env("AGNES_IMAGE_MODEL", "agnes-image-2.1-flash")
VIDEO_MODEL = _env("AGNES_VIDEO_MODEL", "agnes-video-v2.0")

TIMEOUT = int(_env("AGNES_TIMEOUT", "120"))
MAX_RETRIES = int(_env("AGNES_MAX_RETRIES", "2"))


def is_configured() -> bool:
    return bool(AGNES_API_KEY)


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {AGNES_API_KEY}",
        "Content-Type": "application/json",
    }


async def _call_api(
    endpoint: str,
    body: dict,
    timeout: int = TIMEOUT,
) -> dict[str, Any]:
    """Generic API call with retry."""
    last_error = ""
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
                resp = await client.post(
                    f"{AGNES_API_BASE}{endpoint}",
                    headers=_headers(),
                    json=body,
                )
                if resp.status_code != 200:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(1.0 * (attempt + 1))
                        continue
                    return {"_error": last_error}
                return resp.json()
        except httpx.TimeoutException:
            last_error = f"Request timed out after {timeout}s"
            if attempt < MAX_RETRIES:
                await asyncio.sleep(2.0)
                continue
            return {"_error": last_error}
        except Exception as exc:
            last_error = str(exc)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(1.0)
                continue
            return {"_error": last_error}
    return {"_error": last_error}


# ═══════════════════════════════════════════════════════════
# Text / Chat Completions
# ═══════════════════════════════════════════════════════════

async def chat_completion(
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    json_mode: bool = False,
) -> dict[str, Any]:
    """Single-turn text chat. Returns parsed JSON if json_mode=True, else {"content": "..."}."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    body: dict = {
        "model": model or TEXT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    data = await _call_api("/chat/completions", body)
    if "_error" in data:
        return data

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

    if json_mode:
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            # Try extracting from code fences
            for fence in ("```json", "```"):
                if fence in content:
                    inner = content.split(fence, 1)[1]
                    if "```" in inner:
                        inner = inner.split("```", 1)[0]
                    try:
                        return json.loads(inner.strip())
                    except (json.JSONDecodeError, TypeError):
                        pass
            return {"_raw": content, "_error": "Failed to parse JSON response"}

    return {"content": content}


# ═══════════════════════════════════════════════════════════
# Image Generation
# ═══════════════════════════════════════════════════════════

async def generate_image(
    prompt: str,
    size: str = "1792x1024",
    model: str | None = None,
) -> bytes | None:
    """Generate an image and return PNG bytes.

    Supported sizes: 1024x768, 1024x1024, 768x1024, 1792x1024.
    Returns None on failure.
    """
    body: dict = {
        "model": model or IMAGE_MODEL,
        "prompt": prompt,
        "size": size,
    }
    data = await _call_api("/images/generations", body, timeout=120)
    if "_error" in data:
        return None

    # Response: {"data": [{"url": "..."}]} or {"data": [{"b64_json": "..."}]}
    images = data.get("data", [])
    if not images:
        return None

    image_data = images[0]
    url = image_data.get("url")
    if url:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60)) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.content
        except Exception:
            pass

    b64_str = image_data.get("b64_json")
    if b64_str:
        try:
            return b64.b64decode(b64_str)
        except Exception:
            pass

    return None


# ═══════════════════════════════════════════════════════════
# Video Generation (async submit + poll)
# ═══════════════════════════════════════════════════════════

async def submit_video(
    prompt: str,
    num_frames: int = 121,
    frame_rate: int = 25,
    model: str | None = None,
    extra_body: dict | None = None,
) -> str | None:
    """Submit a video generation task. Returns task_id or None."""
    body: dict = {
        "model": model or VIDEO_MODEL,
        "prompt": prompt,
        "num_frames": num_frames,
        "frame_rate": frame_rate,
    }
    if extra_body:
        body["extra_body"] = extra_body

    data = await _call_api("/videos", body, timeout=30)
    if "_error" in data:
        return None
    return data.get("id") or data.get("task_id")


async def poll_video(task_id: str, poll_interval: float = 5.0, max_wait: float = 300.0) -> dict[str, Any]:
    """Poll video task until complete or timeout. Returns {"url": "...", "status": "completed"} or error dict."""
    elapsed = 0.0
    while elapsed < max_wait:
        data = await _call_api(f"/videos/{task_id}", {}, timeout=30)
        if "_error" in data:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            continue

        status = data.get("status") or data.get("state", "")
        if status in ("completed", "succeeded", "done"):
            url = data.get("url") or data.get("video_url") or ""
            if not url and "result" in data:
                url = data["result"].get("url", "") if isinstance(data["result"], dict) else ""
            return {"url": url, "status": "completed"}
        if status in ("failed", "error", "cancelled"):
            return {"_error": f"Video generation failed: {data}"}

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    return {"_error": f"Video generation timed out after {max_wait}s"}


async def download_video(url: str, output_path: str) -> bool:
    """Download generated video to local path."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return True
    except Exception:
        pass
    return False
