"""Unified link parser — handles douyin share links natively, falls back to yt-dlp."""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

YT_DLP_PATH = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "yt-dlp"

PLATFORM_PATTERNS: list[tuple[str, str]] = [
    ("douyin.com", "抖音"),
    ("tiktok.com", "TikTok"),
    ("xiaohongshu.com", "小红书"),
    ("xhslink.com", "小红书"),
    ("bilibili.com", "B站"),
    ("b23.tv", "B站"),
    ("kuaishou.com", "快手"),
    ("youtube.com", "YouTube"),
    ("youtu.be", "YouTube"),
    ("weixin.qq.com", "视频号"),
    ("channels.weixin.qq.com", "视频号"),
]

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)


@dataclass
class ParseResult:
    url: str
    platform: str = ""
    title: str = ""
    author: str = ""
    description: str = ""
    thumbnail_url: str = ""
    parsed: bool = False
    error: str = ""
    raw_metadata: dict[str, Any] = field(default_factory=dict)


def detect_platform(url: str) -> str:
    for pattern, name in PLATFORM_PATTERNS:
        if pattern in url.lower():
            return name
    return "未知"


def _extract_json_blocks(html: str, key_field: str = "aweme_id") -> list[dict]:
    """Extract JSON objects containing a specific key field from HTML."""
    results = []
    for match in re.finditer(r'\{', html):
        start = match.start()
        depth = 1
        in_string = False
        escaped = False
        for i in range(start + 1, min(len(html), start + 50000)):
            ch = html[i]
            if escaped:
                escaped = False
                continue
            if ch == '\\':
                escaped = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    json_str = html[start:i + 1]
                    if key_field in json_str and len(json_str) > 200:
                        try:
                            data = json.loads(json_str)
                            if key_field in data:
                                results.append(data)
                        except json.JSONDecodeError:
                            pass
                    break
    return results


async def _parse_douyin(url: str) -> ParseResult:
    """Parse douyin short link by resolving redirect and extracting embedded JSON."""
    result = ParseResult(url=url, platform="抖音")

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30), follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": MOBILE_UA,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
            )
            html = resp.text
            final_url = str(resp.url) if hasattr(resp, 'url') else url

            # Extract video ID from final URL
            vid_match = re.search(r'/video/(\d+)', final_url)
            video_id = vid_match.group(1) if vid_match else ""

            # Find the aweme data JSON block
            blocks = _extract_json_blocks(html, "aweme_id")
            if not blocks:
                result.error = "未在页面中找到视频数据"
                return result

            # Use the block with the most fields (most complete data)
            data = max(blocks, key=lambda b: len(b))

            result.title = data.get("desc", "")
            result.description = data.get("desc", "")
            author_info = data.get("author", {})
            result.author = author_info.get("nickname", "") if isinstance(author_info, dict) else ""

            # Thumbnail / cover
            video_info = data.get("video", {})
            if isinstance(video_info, dict):
                cover = video_info.get("cover", {})
                if isinstance(cover, dict):
                    urls = cover.get("url_list", [])
                    if urls:
                        result.thumbnail_url = urls[0]
                # Also get duration
                result.raw_metadata["duration"] = video_info.get("duration", 0)
                result.raw_metadata["video_url"] = _video_play_url(video_info)

            # Statistics
            stats = data.get("statistics", {})
            if isinstance(stats, dict):
                result.raw_metadata["statistics"] = stats

            result.raw_metadata["video_id"] = video_id or data.get("aweme_id", "")
            result.raw_metadata["author"] = author_info
            result.parsed = True

        return result
    except httpx.TimeoutException:
        result.error = "请求超时"
        return result
    except Exception as exc:
        result.error = f"解析失败: {str(exc)}"
        return result


async def parse_link(url: str) -> ParseResult:
    """Parse a video/share link and return structured metadata."""
    platform = detect_platform(url)

    # Handle douyin links natively (bypasses yt-dlp cookie requirement)
    if platform == "抖音":
        return await _parse_douyin(url)

    # Fallback: use yt-dlp for other platforms
    result = ParseResult(url=url, platform=platform)

    try:
        metadata = await _run_yt_dlp(url)
        if metadata:
            result.title = metadata.get("title", "")
            result.author = _extract_author(metadata)
            result.description = metadata.get("description", "") or ""
            result.thumbnail_url = metadata.get("thumbnail", "") or ""
            result.platform = _resolve_platform(metadata, platform)
            result.parsed = True
            result.raw_metadata = metadata
        else:
            result.error = "yt-dlp 未能提取到信息"
    except Exception as exc:
        result.error = f"解析失败: {str(exc)}"

    return result


def _video_play_url(video_info: dict[str, Any]) -> str:
    for key in ("play_addr", "play_addr_h264", "download_addr"):
        address = video_info.get(key, {})
        if not isinstance(address, dict):
            continue
        urls = address.get("url_list", [])
        if isinstance(urls, list) and urls:
            return str(urls[0])
    return ""


async def _run_yt_dlp(url: str, cookies_from_browser: str = "") -> dict[str, Any] | None:
    """Call yt-dlp and return extracted info dict."""
    cmd = [
        str(YT_DLP_PATH),
        url,
        "--dump-json",
        "--no-playlist",
        "--no-download",
        "--no-check-certificates",
        "--socket-timeout", "20",
        "--retries", "2",
    ]

    # Optionally use browser cookies
    if cookies_from_browser:
        cmd.extend(["--cookies-from-browser", cookies_from_browser])
    else:
        cmd.extend(["--quiet", "--no-warnings"])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _stderr = await asyncio.wait_for(
            proc.communicate(), timeout=30.0
        )
        if proc.returncode != 0 or not stdout.strip():
            return None

        data = json.loads(stdout.decode("utf-8"))
        return data
    except asyncio.TimeoutError:
        return None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    except FileNotFoundError:
        return None


def _extract_author(metadata: dict[str, Any]) -> str:
    for key in ("uploader", "channel", "creator", "uploader_id"):
        val = metadata.get(key)
        if val:
            return str(val)
    return ""


def _resolve_platform(metadata: dict[str, Any], fallback: str) -> str:
    extractor = (metadata.get("extractor_key") or "").lower()
    mapping = {
        "douyin": "抖音",
        "tiktok": "TikTok",
        "bilibili": "B站",
        "kuaishou": "快手",
        "youtube": "YouTube",
        "xiaohongshu": "小红书",
    }
    for key, label in mapping.items():
        if key in extractor:
            return label
    return fallback
