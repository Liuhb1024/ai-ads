"""Edge TTS client — free, natural-sounding Chinese text-to-speech.

Uses Microsoft Edge's free TTS service via the edge-tts library.
Returns audio + word-level subtitle timestamps for video sync.
"""

from __future__ import annotations

import asyncio
import os
import re
import tempfile
from pathlib import Path
from typing import Any

_DEFAULT_VOICE = "zh-CN-YunxiNeural"  # Male, calm, authoritative — good for ad analysis
_FALLBACK_VOICE = "zh-CN-XiaoxiaoNeural"  # Female, clear, energetic


async def generate_speech(
    text: str,
    output_dir: str,
    voice: str = _DEFAULT_VOICE,
    filename_prefix: str = "narration",
) -> dict[str, Any]:
    """Generate TTS audio + subtitle timestamps.

    Args:
        text: Chinese text to synthesize.
        output_dir: Directory to save mp3 and vtt files.
        voice: Edge TTS voice name. zh-CN-YunxiNeural (male) or zh-CN-XiaoxiaoNeural (female).
        filename_prefix: Prefix for output files.

    Returns:
        {"mp3_path": str, "duration": float, "words": [{"word": str, "start": float, "end": float}]}
        Returns error dict with "_error" key on failure.
    """
    try:
        from edge_tts import Communicate
    except ImportError:
        return {"_error": "edge-tts not installed. Run: pip install edge-tts"}

    os.makedirs(output_dir, exist_ok=True)
    mp3_path = os.path.join(output_dir, f"{filename_prefix}.mp3")
    vtt_path = os.path.join(output_dir, f"{filename_prefix}.vtt")

    try:
        communicate = Communicate(text, voice)
        await communicate.save(mp3_path)
    except Exception:
        # Try fallback voice
        try:
            communicate = Communicate(text, _FALLBACK_VOICE)
            await communicate.save(mp3_path)
        except Exception as exc:
            return {"_error": f"Edge TTS failed: {exc}"}

    # Generate subtitles separately (edge-tts can't do both in one call)
    try:
        sub_communicate = Communicate(text, voice)
        sub_data = await sub_communicate.save(vtt_path, write_media=False)
    except Exception:
        # Subtitles failed but audio succeeded — still usable
        duration = _estimate_duration(text)
        return {"mp3_path": mp3_path, "duration": duration, "words": []}

    # Parse VTT to get word timestamps
    words, duration = _parse_vtt(vtt_path)

    # Clean up vtt file
    try:
        os.remove(vtt_path)
    except OSError:
        pass

    return {"mp3_path": mp3_path, "duration": duration, "words": words}


async def generate_scene_speech(
    scenes: list[dict],
    output_dir: str,
    voice: str = _DEFAULT_VOICE,
) -> list[dict]:
    """Generate TTS for all scenes in parallel.

    Each scene dict should have a "narration" key with the text.
    Returns scenes enriched with "audio_path" and "words" keys.
    """
    tasks = []
    for i, scene in enumerate(scenes):
        text = scene.get("narration", "")
        if text.strip():
            tasks.append(generate_speech(text, output_dir, voice, f"scene_{i:02d}"))
        else:
            tasks.append(asyncio.sleep(0, result={"mp3_path": "", "duration": 0, "words": []}))

    results = await asyncio.gather(*tasks)

    enriched = []
    for scene, result in zip(scenes, results):
        enriched.append({
            **scene,
            "audio_path": result.get("mp3_path", ""),
            "audio_duration": result.get("duration", 0),
            "words": result.get("words", []),
        })

    return enriched


def _parse_vtt(vtt_path: str) -> tuple[list[dict], float]:
    """Parse WebVTT subtitle file to extract word timestamps and total duration."""
    try:
        with open(vtt_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return [], 0.0

    words: list[dict] = []
    max_end = 0.0

    # Match cue blocks: timestamp line + text line(s)
    cue_pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\s*\n(.*?)(?=\n\n|\n\d|\Z)",
        re.DOTALL,
    )

    for match in cue_pattern.finditer(content):
        start = _ts_to_seconds(match.group(1))
        end = _ts_to_seconds(match.group(2))
        text = match.group(3).strip()
        if text:
            words.append({"word": text, "start": start, "end": end})
            if end > max_end:
                max_end = end

    # Try simpler line-by-line fallback for different VTT formats
    if not words:
        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            m = re.match(r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})", line)
            if m:
                start = _ts_to_seconds(m.group(1))
                end = _ts_to_seconds(m.group(2))
                # Collect text from following lines until blank or next timestamp
                text_parts = []
                i += 1
                while i < len(lines) and lines[i].strip() and not re.match(r"\d{2}:\d{2}:\d{2}\.\d{3}", lines[i]):
                    text_parts.append(lines[i].strip())
                    i += 1
                text = " ".join(text_parts)
                if text:
                    words.append({"word": text, "start": start, "end": end})
                    if end > max_end:
                        max_end = end
            else:
                i += 1

    return words, max_end


def _ts_to_seconds(ts: str) -> float:
    """Convert 'HH:MM:SS.mmm' to seconds."""
    parts = ts.replace(".", ":").split(":")
    h, m, s, ms = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    return h * 3600 + m * 60 + s + ms / 1000.0


def _estimate_duration(text: str) -> float:
    """Rough estimate of speech duration for Chinese text (characters per second)."""
    # Chinese TTS ~3-4 chars/second
    return max(1.0, len(text.replace(" ", "")) / 3.5)
