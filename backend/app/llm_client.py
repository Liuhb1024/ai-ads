"""Async DMXAPI client — OpenAI-compatible chat completions with retry."""

from __future__ import annotations

import json
import os
import asyncio
from typing import Any

import httpx


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


BASE_URL = _env("DMXAPI_BASE_URL", "https://www.dmxapi.cn/v1")
API_KEY = _env("DMXAPI_API_KEY")
DEFAULT_MODEL = _env("DEFAULT_LLM_MODEL", "claude-haiku-4-5-20251001")
VISION_MODEL = _env("VISION_MODEL", "gpt-5.4-nano")
VIDEO_MODEL = _env("DOUBAO_VIDEO_MODEL", "doubao-seed-2-0-lite-260215")
TIMEOUT = int(_env("LLM_TIMEOUT", "120"))
MAX_RETRIES = int(_env("LLM_MAX_RETRIES", "1"))
TEMPERATURE = float(_env("LLM_TEMPERATURE", "0.7"))
MAX_TOKENS = int(_env("LLM_MAX_TOKENS", "4096"))


def is_configured() -> bool:
    return bool(API_KEY)


def _extract_json(text: str) -> dict | None:
    """Extract and parse JSON from LLM response, handling code fences and truncation."""
    if not text or not text.strip():
        return None

    # 1. Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 2. Extract from code fences
    block = text
    for fence in ("```json", "```"):
        if fence in block:
            parts = block.split(fence, 1)
            if len(parts) > 1:
                inner = parts[1]
                if "```" in inner:
                    inner = inner.split("```", 1)[0]
                block = inner.strip()
                break

    # 3. Try parsed extracted block
    try:
        return json.loads(block)
    except json.JSONDecodeError:
        pass

    # 4. Try to salvage truncated JSON by counting and closing unclosed braces/brackets
    # Only attempt for reasonably sized blocks
    if len(block) > 100 and block[0] in ("{", "["):
        # Count open vs close
        pairs = {"{": "}", "[": "]"}
        stack = []
        in_string = False
        escaped = False
        for ch in block:
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch in pairs:
                stack.append(pairs[ch])
            elif ch in (")", "}", "]"):
                if stack and stack[-1] == ch:
                    stack.pop()
                # else: stray closing bracket, ignore

        if stack:
            # Close unclosed structures from innermost out
            suffix = "".join(reversed(stack))
            try:
                return json.loads(block + suffix)
            except json.JSONDecodeError:
                pass

    return None


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


async def chat_completion(
    *,
    model: str | None = None,
    system: str,
    user: str,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
    response_format: dict | None = None,
) -> dict[str, Any]:
    """Single-turn text chat completion. Returns parsed JSON if response_format is json_object."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return await _call_api(model or DEFAULT_MODEL, messages, temperature, max_tokens, response_format)


async def chat_completion_vision(
    *,
    model: str | None = None,
    system: str,
    text: str,
    images: list[dict],  # [{"base64": "...", "mime": "image/jpeg"}, ...]
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
    response_format: dict | None = None,
) -> dict[str, Any]:
    """Multimodal chat completion with base64-encoded images."""
    content: list[dict] = [{"type": "text", "text": text}]
    for img in images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{img['mime']};base64,{img['base64']}"},
        })

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ]
    return await _call_api(model or VISION_MODEL, messages, temperature, max_tokens, response_format)


async def chat_completion_video(
    *,
    model: str | None = None,
    system: str,
    text: str,
    video_path: str | None = None,
    video_url: str | None = None,
    video_base64: str | None = None,
    fps: float = 1.0,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
    response_format: dict | None = None,
) -> dict[str, Any]:
    """Chat completion with video input via doubao's video_url format.

    Provide one of: video_path (local file), video_url (remote), or video_base64 (pre-encoded).
    """
    content: list[dict] = [{"type": "text", "text": text}]

    # Determine video source
    if video_base64:
        url = video_base64
    elif video_path:
        b64 = _video_to_base64(video_path)
        if not b64:
            return {"_error": f"Failed to encode video: {video_path}"}
        url = b64
    elif video_url:
        url = video_url
    else:
        return {"_error": "No video source provided"}

    content.append({
        "type": "video_url",
        "video_url": {"url": url, "fps": fps},
    })

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ]
    return await _call_api(model or VIDEO_MODEL, messages, temperature, max_tokens, response_format)


def _video_to_base64(file_path: str) -> str | None:
    """Encode video file to base64 data URL."""
    import base64 as b64
    from pathlib import Path
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "rb") as f:
            data = b64.b64encode(f.read()).decode("ascii")
        ext = Path(file_path).suffix.lower()
        mime_map = {".mp4": "video/mp4", ".webm": "video/webm", ".mkv": "video/x-matroska"}
        mime = mime_map.get(ext, "video/mp4")
        return f"data:{mime};base64,{data}"
    except Exception:
        return None


async def _call_api(
    model: str,
    messages: list,
    temperature: float,
    max_tokens: int,
    response_format: dict | None,
) -> dict[str, Any]:
    body: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        body["response_format"] = response_format

    last_error = ""
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT)) as client:
                resp = await client.post(
                    f"{BASE_URL}/chat/completions",
                    headers=_headers(),
                    json=body,
                )
                if resp.status_code != 200:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(1.0 * (attempt + 1))
                        continue
                    return {"_error": last_error}

                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Try to parse JSON from response
                if response_format and isinstance(response_format, dict) and response_format.get("type") == "json_object":
                    parsed = _extract_json(content)
                    if parsed is not None:
                        return parsed
                    return {"_raw": content, "_error": "Failed to parse JSON response"}

                return {"content": content}

        except httpx.TimeoutException:
            last_error = f"Request timed out after {TIMEOUT}s"
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
