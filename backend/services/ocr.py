"""Visual / text-overlay extraction from video frames.

For now, saves frame metadata and exports base64 snapshots for Vision LLM analysis.
Full OCR (EasyOCR/PaddleOCR) can be added later.
"""

from __future__ import annotations

import base64
import os
from typing import Any


def frame_to_base64(frame_path: str, max_size: tuple = (720, 720)) -> str | None:
    """Read a frame image and return a base64-encoded JPEG string.

    Resizes if needed to keep payload small for LLM Vision API.
    """
    try:
        from PIL import Image
    except ImportError:
        return None

    if not os.path.exists(frame_path):
        return None

    img = Image.open(frame_path)
    img.thumbnail(max_size, Image.LANCZOS)

    from io import BytesIO
    buf = BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def frames_metadata(frames: list[dict]) -> list[dict]:
    """Enrich frame metadata with image dimensions."""
    try:
        from PIL import Image
    except ImportError:
        return frames

    for f in frames:
        path = f.get("path", "")
        if path and os.path.exists(path):
            try:
                img = Image.open(path)
                f["width"], f["height"] = img.size
            except Exception:
                f["width"], f["height"] = 0, 0
    return frames


def frames_to_base64_list(
    frames: list[dict],
    max_frames: int = 10,
) -> list[dict[str, Any]]:
    """Convert frames to a list of {timestamp, base64} for Vision API."""
    step = max(1, len(frames) // max_frames)
    sampled = frames[::step][:max_frames]

    results = []
    for f in sampled:
        b64 = frame_to_base64(f["path"])
        if b64:
            results.append({
                "timestamp": f.get("timestamp", 0),
                "base64": b64,
                "mime_type": "image/jpeg",
            })
    return results
