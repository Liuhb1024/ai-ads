"""Speech transcription using faster-whisper."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

import shutil

FFMPEG_PATH = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"

# Lazy-loaded singleton
_model = None
_model_size = "medium"
_model_device = "auto"
_compute_type = "int8"


def _get_model():
    """Lazy-load the Whisper model (downloaded on first use, ~3GB)."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(
            _model_size,
            device=_model_device,
            compute_type=_compute_type,
            download_root=str(Path.home() / ".cache" / "faster-whisper"),
        )
    return _model


def _transcribe_sync(
    audio_path: str,
    language: str | None = "zh",
    beam_size: int = 5,
) -> tuple[list[dict], object]:
    """Synchronous wrapper so transcription can run in a thread pool."""
    model = _get_model()
    segments_data, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=beam_size,
        vad_filter=True,
    )
    results = [
        {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
        for s in segments_data
    ]
    return results, info


async def extract_audio(video_path: str, output_path: str | None = None) -> str:
    """Extract audio from video as 16kHz mono WAV for Whisper."""
    if output_path is None:
        output_dir = tempfile.mkdtemp(prefix="ad_audio_")
        output_path = os.path.join(output_dir, "audio.wav")

    cmd = [
        FFMPEG_PATH,
        "-i", video_path,
        "-vn",               # no video
        "-acodec", "pcm_s16le",
        "-ar", "16000",      # 16kHz
        "-ac", "1",          # mono
        "-y",
        output_path,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()

    if proc.returncode != 0 or not os.path.exists(output_path):
        raise RuntimeError("Audio extraction failed")

    return output_path


async def transcribe(
    audio_path: str,
    language: str | None = "zh",
    beam_size: int = 5,
) -> list[dict]:
    """Transcribe audio to text with timestamps.

    Returns a list of segments: [{start, end, text}]
    """
    loop = asyncio.get_running_loop()
    results, _info = await loop.run_in_executor(
        None, _transcribe_sync, audio_path, language, beam_size,
    )
    return results


async def transcribe_video(
    video_path: str,
    language: str | None = "zh",
) -> dict:
    """Convenience: extract audio + transcribe a video file.

    Returns:
        {
            "full_text": str,
            "segments": [{start, end, text}],
            "duration": float,
            "language": str,
            "language_probability": float,
        }
    """
    audio_path = await extract_audio(video_path)

    loop = asyncio.get_running_loop()
    segments, info = await loop.run_in_executor(
        None, _transcribe_sync, audio_path, language, 5,
    )

    # Cleanup temp audio
    try:
        os.remove(audio_path)
    except OSError:
        pass

    return {
        "full_text": " ".join(s["text"] for s in segments),
        "segments": segments,
        "duration": info.duration,
        "language": info.language,
        "language_probability": round(info.language_probability, 4),
    }
