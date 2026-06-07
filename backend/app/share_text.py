from __future__ import annotations

import re
from urllib.parse import urlparse


SUPPORTED_HOST_SUFFIXES = (
    "douyin.com",
    "tiktok.com",
    "xiaohongshu.com",
    "xhslink.com",
    "bilibili.com",
    "b23.tv",
    "kuaishou.com",
    "youtube.com",
    "youtu.be",
    "weixin.qq.com",
    "channels.weixin.qq.com",
)

URL_PATTERN = re.compile(r"https?://[^\s<>\"，。！？；：、]+", re.IGNORECASE)
TRAILING_PUNCTUATION = "，。！？；：、,.;:!?)]}》」』】"


class ShareTextError(ValueError):
    pass


def extract_supported_url(text: str) -> str:
    if not text or not text.strip():
        raise ShareTextError("请粘贴平台分享链接或完整分享口令")

    matches = URL_PATTERN.findall(text)
    if not matches:
        raise ShareTextError("没有识别到有效链接，请粘贴完整的平台分享内容")

    for raw_url in matches:
        url = raw_url.rstrip(TRAILING_PUNCTUATION)
        host = (urlparse(url).hostname or "").lower()
        if any(host == suffix or host.endswith(f".{suffix}") for suffix in SUPPORTED_HOST_SUFFIXES):
            return url

    raise ShareTextError("暂不支持该链接，请使用抖音、小红书、B站、快手、YouTube 或视频号链接")
