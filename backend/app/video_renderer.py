"""MoviePy-based video renderer — Ken Burns slideshow, text overlays, subtitles, audio mix.

Target: 1920×1080 landscape, 25fps, H.264 MP4.
Each scene: AI illustration background + text card overlay + synced subtitles + BGM.
"""

from __future__ import annotations

import os
import random
import tempfile
from pathlib import Path
from typing import Any


def render_video(
    scenes: list[dict],
    images: list[str],
    bgm_path: str = "",
    output_path: str = "",
    width: int = 1920,
    height: int = 1080,
    fps: int = 25,
) -> str:
    """Render the final video from scenes and assets.

    Args:
        scenes: List of scene dicts with:
            - audio_path: path to TTS mp3
            - audio_duration: float seconds
            - words: list of {"word", "start", "end"} subtitle entries
            - overlay_text: optional text to display as heading
        images: List of image paths (one per scene, may be empty for text-only scenes).
        bgm_path: Path to background music mp3 (optional).
        output_path: Where to write the mp4. Auto-generated if empty.
        width, height: Output resolution.
        fps: Frame rate.

    Returns:
        Path to the rendered mp4 file.
    """
    if not output_path:
        output_path = tempfile.mktemp(suffix=".mp4")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        return _render_with_moviepy(scenes, images, bgm_path, output_path, width, height, fps)
    except ImportError:
        return _render_with_ffmpeg(scenes, images, bgm_path, output_path, width, height, fps)


def _render_with_moviepy(
    scenes: list[dict],
    images: list[str],
    bgm_path: str,
    output_path: str,
    width: int,
    height: int,
    fps: int,
) -> str:
    """Render using MoviePy for rich effects."""
    from moviepy import (
        AudioFileClip,
        CompositeAudioClip,
        CompositeVideoClip,
        ImageClip,
        TextClip,
        concatenate_videoclips,
    )
    from moviepy.video.fx import CrossFadeIn, CrossFadeOut, Resize

    scene_clips = []

    for i, scene in enumerate(scenes):
        duration = scene.get("audio_duration", 5.0)
        if duration <= 0:
            duration = 5.0

        layers = []

        # Background image with Ken Burns effect
        img_path = images[i] if i < len(images) and images[i] else None
        bg = _create_background(img_path, duration, width, height)
        if bg:
            layers.append(bg)

        # Text overlay (heading)
        overlay = scene.get("overlay_text", "")
        if overlay.strip():
            text_layer = _create_text_overlay(overlay, duration, width, height)
            if text_layer:
                layers.append(text_layer)

        # Subtitle layer
        words = scene.get("words", [])
        if words:
            sub_layer = _create_subtitle_layer(words, duration, width, height)
            if sub_layer:
                layers.append(sub_layer)

        if not layers:
            # Create a blank clip for empty scenes
            from moviepy import ColorClip
            layers.append(ColorClip((width, height), color=(20, 20, 30), duration=duration))

        clip = CompositeVideoClip(layers, size=(width, height)).with_duration(duration)

        # Add cross-fade transitions between scenes
        if i > 0:
            clip = clip.with_effects([CrossFadeIn(0.4)])
        if i < len(scenes) - 1:
            clip = clip.with_effects([CrossFadeOut(0.4)])

        # Attach audio
        audio_path = scene.get("audio_path", "")
        if audio_path and os.path.exists(audio_path):
            try:
                audio = AudioFileClip(audio_path)
                clip = clip.with_audio(audio)
            except Exception:
                pass

        scene_clips.append(clip)

    # Concatenate all scenes
    final = concatenate_videoclips(scene_clips)

    # Mix in background music
    if bgm_path and os.path.exists(bgm_path):
        try:
            from moviepy.audio.fx import AudioLoop, MultiplyVolume

            bgm = AudioFileClip(bgm_path)
            # Loop BGM if shorter than video, cut if longer
            bgm = bgm.with_effects([AudioLoop(duration=final.duration)])
            bgm = bgm.with_effects([MultiplyVolume(0.18)])

            if final.audio:
                final_audio = CompositeAudioClip([final.audio, bgm])
            else:
                final_audio = bgm
            final = final.with_audio(final_audio)
        except Exception:
            pass

    # Write final video
    final.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        bitrate="5000k",
        preset="medium",
        logger=None,
    )
    final.close()

    return output_path


def _create_background(
    img_path: str | None,
    duration: float,
    width: int,
    height: int,
) -> Any | None:
    """Create background clip with Ken Burns effect (slow zoom/pan)."""
    from moviepy import ImageClip, ColorClip
    from moviepy.video.fx import Resize

    if not img_path or not os.path.exists(img_path):
        # Dark gradient-ish background
        return ColorClip((width, height), color=(15, 15, 25), duration=duration)

    clip = ImageClip(img_path, duration=duration)

    # Resize to cover frame (crop if needed)
    clip = clip.resized(height=height)
    if clip.w < width:
        clip = clip.resized(width=width)

    # Ken Burns: subtle zoom in/out + pan
    zoom_direction = random.choice([-1, 1])  # zoom in or out
    pan_x = random.uniform(-0.03, 0.03)
    pan_y = random.uniform(-0.03, 0.03)

    def ken_burns(get_frame, t):
        """Apply zoom and pan at time t."""
        progress = t / duration if duration > 0 else 0
        scale = 1.0 + zoom_direction * 0.06 * progress
        # Scale the image
        import numpy as np
        frame = get_frame(t)
        h, w = frame.shape[:2]

        new_w = int(w * scale)
        new_h = int(h * scale)
        # We'll use a simpler approach: just crop the center with slight offset
        from PIL import Image
        img = Image.fromarray(frame)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # Crop from center with pan offset
        x_offset = int((new_w - w) * (0.5 + pan_x * progress))
        y_offset = int((new_h - h) * (0.5 + pan_y * progress))
        x_offset = max(0, min(x_offset, new_w - w))
        y_offset = max(0, min(y_offset, new_h - h))

        cropped = img.crop((x_offset, y_offset, x_offset + w, y_offset + h))
        return np.array(cropped)

    clip = clip.transform(ken_burns)

    # Crop to exact dimensions
    clip = clip.resized((width, height))

    # Fade in/out
    from moviepy.video.fx import FadeIn, FadeOut
    clip = clip.with_effects([FadeIn(0.3), FadeOut(0.5)])

    return clip


def _create_text_overlay(
    text: str,
    duration: float,
    width: int,
    height: int,
) -> Any | None:
    """Create a text card overlay with fade animation."""
    from moviepy import TextClip
    from moviepy.video.fx import FadeIn, FadeOut

    try:
        # Try system font first, fall back gracefully
        font = "PingFang-SC-Bold" if os.uname().sysname == "Darwin" else "Noto-Sans-CJK-Bold"
        clip = TextClip(
            text=text,
            font=font,
            font_size=72,
            color="white",
            stroke_color="black",
            stroke_width=3,
            size=(int(width * 0.85), None),
            method="caption",
            text_align="center",
            duration=duration,
        )
    except Exception:
        # Fallback: basic text without custom font
        clip = TextClip(
            text=text,
            font_size=56,
            color="white",
            stroke_color="black",
            stroke_width=2,
            size=(int(width * 0.85), None),
            method="caption",
            text_align="center",
            duration=duration,
        )

    clip = clip.with_position(("center", height * 0.35))
    clip = clip.with_effects([FadeIn(0.3), FadeOut(0.4)])

    return clip


def _create_subtitle_layer(
    words: list[dict],
    duration: float,
    width: int,
    height: int,
) -> Any | None:
    """Create a subtitle layer that shows text synced to TTS timing.

    Uses a simple approach: show each word/phrase as a sub-clip at the right time.
    """
    from moviepy import CompositeVideoClip, TextClip

    subtitle_clips = []

    for entry in words:
        text = entry.get("word", "")
        start = entry.get("start", 0.0)
        end = entry.get("end", start + 2.0)
        seg_duration = min(end - start, duration - start)

        if seg_duration <= 0 or not text.strip():
            continue

        try:
            clip = TextClip(
                text=text.strip(),
                font_size=32,
                color="white",
                stroke_color="black",
                stroke_width=2,
                size=(int(width * 0.9), None),
                method="caption",
                text_align="center",
                duration=seg_duration,
            )
            clip = clip.with_position(("center", height * 0.88))
            clip = clip.with_start(start)
            subtitle_clips.append(clip)
        except Exception:
            continue

    if not subtitle_clips:
        return None

    return CompositeVideoClip(subtitle_clips, size=(width, height))


def _render_with_ffmpeg(
    scenes: list[dict],
    images: list[str],
    bgm_path: str,
    output_path: str,
    width: int,
    height: int,
    fps: int,
) -> str:
    """Fallback: basic FFmpeg-based rendering when MoviePy is not installed."""
    import subprocess
    import tempfile

    # Build filter_complex for all scenes
    filter_parts = []
    input_args = []
    concat_inputs = ""

    for i, scene in enumerate(scenes):
        duration = scene.get("audio_duration", 5.0)
        img_path = images[i] if i < len(images) and images[i] else None

        if img_path and os.path.exists(img_path):
            input_args.extend(["-loop", "1", "-t", str(duration), "-i", img_path])
            filter_parts.append(
                f"[{2*i}:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},zoompan=z='min(zoom+0.0005,1.04)':d=1:x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps},"
                f"fade=t=in:d=0.3,fade=t=out:d=0.3:st={duration-0.3},"
                f"setpts=PTS-STARTPTS[v{i}]"
            )
        else:
            # Color background
            input_args.extend(["-f", "lavfi", "-i", f"color=c=0x101020:s={width}x{height}:d={duration}:r={fps}"])
            filter_parts.append(f"[{2*i}:v]fade=t=in:d=0.3,fade=t=out:d=0.3:st={duration-0.3},setpts=PTS-STARTPTS[v{i}]")

        concat_inputs += f"[v{i}]"

        # Add audio
        audio_path = scene.get("audio_path", "")
        if audio_path and os.path.exists(audio_path):
            input_args.extend(["-i", audio_path])
            filter_parts.append(f"[{2*i+1}:a]adelay=0|0[a{i}]")
        else:
            filter_parts.append(f"aevalsrc=0:d={duration}[a{i}]")

    concat_inputs += f"concat=n={len(scenes)}:v=1:a=1[v][a]"

    # Build final command
    cmd = ["ffmpeg", "-y"] + input_args

    filter_complex = ";".join(filter_parts) + ";" + concat_inputs
    cmd.extend(["-filter_complex", filter_complex])

    # Add BGM if available
    if bgm_path and os.path.exists(bgm_path):
        cmd.extend(["-i", bgm_path])
        cmd.extend([
            "-filter_complex",
            f"{filter_complex};"
            f"[a]volume=1.0[main];[3:a]volume=0.18,aloop=loop=-1:size=2e9[bgm];"
            f"[main][bgm]amix=inputs=2:duration=shortest[aout]",
            "-map", "[v]",
            "-map", "[aout]",
        ])
    else:
        cmd.extend(["-map", "[v]", "-map", "[a]"])

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        output_path,
    ])

    subprocess.run(cmd, check=True, capture_output=True, text=True)

    return output_path
