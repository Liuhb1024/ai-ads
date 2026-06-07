"""Pixabay background music downloader.

Uses the free Pixabay API to search and download royalty-free music.
No attribution required for commercial use.
"""

from __future__ import annotations

import os
import httpx


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


PIXABAY_API_KEY = _env("PIXABAY_API_KEY")

_DEFAULT_QUERIES = [
    "corporate ambient",
    "cinematic background",
    "inspirational uplifting",
    "modern business",
]


async def fetch_bgm(
    output_path: str,
    query: str = "",
    min_duration: int = 40,
    max_duration: int = 120,
) -> str | None:
    """Search Pixabay for music matching query, download to output_path.

    Returns the output path on success, None on failure.
    """
    if not PIXABAY_API_KEY:
        return None

    queries = [query] if query.strip() else _DEFAULT_QUERIES

    for q in queries:
        result = await _search_and_download(q, output_path, min_duration, max_duration)
        if result:
            return result

    return None


async def _search_and_download(
    query: str,
    output_path: str,
    min_duration: int,
    max_duration: int,
) -> str | None:
    """Search Pixabay for music matching query and download first match."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30)) as client:
            # Use Pixabay video endpoint with music category filter
            resp = await client.get(
                "https://pixabay.com/api/videos/",
                params={
                    "key": PIXABAY_API_KEY,
                    "q": query,
                    "category": "music",
                    "per_page": 10,
                    "safesearch": "true",
                },
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            hits = data.get("hits", [])

            for hit in hits:
                duration = hit.get("duration", 0)
                if duration < min_duration or duration > max_duration:
                    continue

                # Get the highest quality audio URL
                videos = hit.get("videos", {})
                best = videos.get("large") or videos.get("medium") or videos.get("small")
                if not best:
                    # Try direct download URL from the video
                    url = hit.get("videos", {}).get("tiny", {}).get("url", "")
                    if not url:
                        continue
                else:
                    url = best.get("url", "")
                    if not url:
                        continue

                # Download the audio
                dl_resp = await client.get(url, follow_redirects=True)
                if dl_resp.status_code == 200:
                    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(dl_resp.content)
                    return output_path

    except Exception:
        pass

    return None
