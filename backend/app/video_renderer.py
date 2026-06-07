"""Video renderer — Pillow text → ImageClip overlay, MoviePy compositing.

All Chinese text is pre-rendered as RGBA PNG images via Pillow to guarantee
correct font rendering, then loaded as ImageClip overlays. No TextClip used.
"""

from __future__ import annotations

import os
import random
import struct
import tempfile
from pathlib import Path
from typing import Any


# ═══════════════════════════════════════════════════════════
# Font discovery
# ═══════════════════════════════════════════════════════════

def _find_chinese_font() -> str:
    """Find a Chinese-capable font on the system."""
    candidates = [
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        # Linux
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return fp
    return ""


_CHINESE_FONT = _find_chinese_font()


# ═══════════════════════════════════════════════════════════
# Text → image rendering (Pillow)
# ═══════════════════════════════════════════════════════════

def _text_to_image(
    text: str,
    output_path: str,
    width: int,
    height: int,
    font_size: int = 64,
    color: tuple = (255, 255, 255, 255),
    stroke_color: tuple = (0, 0, 0, 200),
    stroke_width: int = 3,
    position: str = "center",
    bg_color: tuple = (0, 0, 0, 0),
) -> str:
    """Render text to a transparent RGBA PNG using Pillow. Returns output_path."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Load font
    font = None
    if _CHINESE_FONT:
        try:
            font = ImageFont.truetype(_CHINESE_FONT, font_size)
        except Exception:
            pass
    if font is None:
        try:
            font = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    # Word wrap
    lines = _wrap_text(text, font, width - 60)

    # Calculate total height
    line_heights = []
    for line in lines:
        bbox = font.getbbox(line) if hasattr(font, "getbbox") else (0, 0, 0, 0)
        line_heights.append(bbox[3] - bbox[1] if bbox[3] - bbox[1] > 0 else font_size + 8)
    total_h = sum(line_heights) + (len(lines) - 1) * 8

    y_start = (height - total_h) / 2

    for i, line in enumerate(lines):
        bbox = font.getbbox(line) if hasattr(font, "getbbox") else (0, 0, 0, 0)
        line_w = bbox[2] - bbox[0] if bbox[2] - bbox[0] > 0 else len(line) * font_size * 0.6
        x = (width - line_w) / 2
        y = y_start + sum(line_heights[:i]) + i * 8

        # Stroke (text shadow / outline)
        if stroke_width > 0:
            for dx in (-stroke_width, 0, stroke_width):
                for dy in (-stroke_width, 0, stroke_width):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x + dx, y + dy), line, font=font, fill=stroke_color)
        # Main text
        draw.text((x, y), line, font=font, fill=color)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


def _wrap_text(text: str, font: Any, max_width: int) -> list[str]:
    """Simple word wrap for Chinese text (char-level wrapping)."""
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for ch in paragraph:
            test = current + ch
            try:
                bbox = font.getbbox(test)
                w = bbox[2] - bbox[0]
            except Exception:
                w = len(test) * 30
            if w > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
    return lines if lines else [text]


# ═══════════════════════════════════════════════════════════
# Audio validation
# ═══════════════════════════════════════════════════════════

def _is_valid_audio(path: str) -> bool:
    """Check that an audio file exists, has size, and appears to be valid."""
    if not path or not os.path.exists(path):
        return False
    size = os.path.getsize(path)
    if size < 100:
        return False
    # Quick check: MP3 files start with ID3 or sync word
    if path.endswith(".mp3"):
        with open(path, "rb") as f:
            header = f.read(3)
        return header in (b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")
    return True


# ═══════════════════════════════════════════════════════════
# Main render pipeline
# ═══════════════════════════════════════════════════════════

def render_video(
    scenes: list[dict],
    images: list[str],
    bgm_path: str = "",
    output_path: str = "",
    width: int = 1920,
    height: int = 1080,
    fps: int = 25,
) -> str:
    """Render the final video from scenes and assets."""
    if not output_path:
        output_path = tempfile.mktemp(suffix=".mp4")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        return _render_with_moviepy(scenes, images, bgm_path, output_path, width, height, fps)
    except Exception:
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
    """Render using MoviePy with Pillow-rendered text overlays."""
    from moviepy import (
        AudioFileClip,
        CompositeAudioClip,
        CompositeVideoClip,
        ImageClip,
        concatenate_videoclips,
    )
    from moviepy.video.fx import CrossFadeIn, CrossFadeOut, FadeIn, FadeOut

    scene_clips = []
    text_temp_dir = os.path.join(os.path.dirname(output_path), "text_overlays")
    os.makedirs(text_temp_dir, exist_ok=True)

    for i, scene in enumerate(scenes):
        duration = scene.get("audio_duration", scene.get("duration", 5.0))
        if duration <= 0:
            duration = 5.0

        layers = []

        # Background image with Ken Burns effect
        img_path = images[i] if i < len(images) and images[i] else None
        bg = _create_background(img_path, duration, width, height)
        if bg:
            layers.append(bg)

        # Text overlay — rendered via Pillow
        overlay_text = scene.get("overlay_text", "")
        if overlay_text.strip():
            overlay_img = os.path.join(text_temp_dir, f"overlay_{i:02d}.png")
            _text_to_image(
                overlay_text, overlay_img,
                width, int(height * 0.4),
                font_size=72,
                color=(255, 250, 240, 255),
                stroke_color=(0, 0, 0, 200),
                stroke_width=3,
            )
            if os.path.exists(overlay_img):
                text_clip = ImageClip(overlay_img, duration=duration)
                text_clip = text_clip.resized(width=int(width * 0.85))
                text_clip = text_clip.with_position(("center", int(height * 0.12)))
                text_clip = text_clip.with_effects([FadeIn(0.3), FadeOut(0.4)])
                layers.append(text_clip)

        # Subtitle — rendered via Pillow
        words = scene.get("words", [])
        if words:
            sub_clips = _create_subtitles_from_words(words, duration, width, height, text_temp_dir, i)
            if sub_clips:
                layers.append(sub_clips)

        if not layers:
            from moviepy import ColorClip
            layers.append(ColorClip((width, height), color=(15, 15, 25), duration=duration))

        clip = CompositeVideoClip(layers, size=(width, height)).with_duration(duration)

        # Cross-fade transitions
        if i > 0:
            clip = clip.with_effects([CrossFadeIn(0.4)])
        if i < len(scenes) - 1:
            clip = clip.with_effects([CrossFadeOut(0.4)])

        # Attach TTS audio
        audio_path = scene.get("audio_path", "")
        if _is_valid_audio(audio_path):
            try:
                audio = AudioFileClip(audio_path)
                if audio.duration > 0:
                    clip = clip.with_audio(audio)
            except Exception:
                pass

        scene_clips.append(clip)

    # Concatenate
    final = concatenate_videoclips(scene_clips)

    # Mix BGM
    if _is_valid_audio(bgm_path):
        try:
            from moviepy.audio.fx import AudioLoop
            from moviepy.video.fx import MultiplyVolume

            bgm = AudioFileClip(bgm_path)
            if bgm.duration > 0:
                bgm = bgm.with_effects([AudioLoop(duration=final.duration)])
                bgm = bgm.with_effects([MultiplyVolume(0.18)])

                if final.audio:
                    final_audio = CompositeAudioClip([final.audio, bgm])
                else:
                    final_audio = bgm
                final = final.with_audio(final_audio)
        except Exception:
            pass

    # Write
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


def _create_subtitles_from_words(
    words: list[dict],
    duration: float,
    width: int,
    height: int,
    temp_dir: str,
    scene_idx: int,
):
    """Create a subtitle CompositeVideoClip from word timings using Pillow images."""
    from moviepy import CompositeVideoClip, ImageClip

    sub_clips = []

    for j, entry in enumerate(words):
        text = entry.get("word", "")
        start = entry.get("start", 0.0)
        end = entry.get("end", start + 2.0)
        seg_dur = min(end - start, duration - start)

        if seg_dur <= 0.1 or not text.strip():
            continue

        sub_img = os.path.join(temp_dir, f"sub_{scene_idx:02d}_{j:02d}.png")
        _text_to_image(
            text, sub_img,
            int(width * 0.9), 90,
            font_size=36,
            color=(255, 255, 255, 255),
            stroke_color=(0, 0, 0, 220),
            stroke_width=2,
        )
        if os.path.exists(sub_img):
            try:
                clip = ImageClip(sub_img, duration=seg_dur)
                clip = clip.resized(width=int(width * 0.9))
                clip = clip.with_position(("center", int(height * 0.86)))
                clip = clip.with_start(start)
                sub_clips.append(clip)
            except Exception:
                continue

    if not sub_clips:
        return None

    return CompositeVideoClip(sub_clips, size=(width, height))


def _create_background(
    img_path: str | None,
    duration: float,
    width: int,
    height: int,
):
    """Create background clip with Ken Burns effect."""
    from moviepy import ImageClip, ColorClip
    from moviepy.video.fx import FadeIn, FadeOut

    if not img_path or not os.path.exists(img_path):
        return ColorClip((width, height), color=(15, 15, 25), duration=duration)

    clip = ImageClip(img_path, duration=duration)

    # Resize to cover frame
    clip = clip.resized(height=height)
    if clip.w < width:
        clip = clip.resized(width=width)

    # Ken Burns transform
    zoom_dir = random.choice([-1, 1])
    pan_x = random.uniform(-0.03, 0.03)
    pan_y = random.uniform(-0.03, 0.03)

    def ken_burns(get_frame, t):
        import numpy as np
        progress = t / duration if duration > 0 else 0
        scale = 1.0 + zoom_dir * 0.06 * progress
        frame = get_frame(t)
        h, w = frame.shape[:2]
        new_w, new_h = int(w * scale), int(h * scale)

        from PIL import Image
        img = Image.fromarray(frame)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        xo = int((new_w - w) * (0.5 + pan_x * progress))
        yo = int((new_h - h) * (0.5 + pan_y * progress))
        xo = max(0, min(xo, new_w - w))
        yo = max(0, min(yo, new_h - h))

        return np.array(img.crop((xo, yo, xo + w, yo + h)))

    clip = clip.transform(ken_burns)
    clip = clip.resized((width, height))
    clip = clip.with_effects([FadeIn(0.3), FadeOut(0.5)])

    return clip


# ═══════════════════════════════════════════════════════════
# FFmpeg fallback
# ═══════════════════════════════════════════════════════════

def _render_with_ffmpeg(
    scenes: list[dict],
    images: list[str],
    bgm_path: str,
    output_path: str,
    width: int,
    height: int,
    fps: int,
) -> str:
    """Fallback: basic FFmpeg rendering with Pillow text overlays."""
    import subprocess
    import tempfile

    text_temp_dir = os.path.join(os.path.dirname(output_path), "text_overlays")
    os.makedirs(text_temp_dir, exist_ok=True)

    filter_parts = []
    input_args = []
    audio_inputs = 0
    concat_v = ""
    concat_a = ""

    for i, scene in enumerate(scenes):
        duration = scene.get("audio_duration", scene.get("duration", 5.0))
        if duration <= 0:
            duration = 5.0

        # Background
        img_path = images[i] if i < len(images) and images[i] else None
        if img_path and os.path.exists(img_path):
            input_args.extend(["-loop", "1", "-t", str(duration), "-i", img_path])
            vi = 2 * i + audio_inputs
            base = f"[{vi}:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
        else:
            input_args.extend(["-f", "lavfi", "-i", f"color=c=0x0F0F19:s={width}x{height}:d={duration}:r={fps}"])
            vi = 2 * i + audio_inputs
            base = f"[{vi}:v]"

        # Ken Burns zoom
        base += f",zoompan=z='min(zoom+0.0005,1.04)':d=1:s={width}x{height}:fps={fps}"

        # Add text overlay image
        overlay_text = scene.get("overlay_text", "")
        text_overlay_filter = ""
        if overlay_text.strip():
            overlay_img = os.path.join(text_temp_dir, f"overlay_ff_{i:02d}.png")
            _text_to_image(
                overlay_text, overlay_img,
                int(width * 0.85), int(height * 0.4),
                font_size=72,
                color=(255, 250, 240, 255),
                stroke_color=(0, 0, 0, 200),
                stroke_width=3,
            )
            if os.path.exists(overlay_img):
                input_args.extend(["-i", overlay_img])
                oi = len(input_args) // 2  # approximate
                text_overlay_filter = f"[{oi-1}:v]scale={int(width*0.85)}:-1[ov{i}];{base}[ov{i}]overlay=(W-w)/2:H*0.12"

        if text_overlay_filter:
            base = text_overlay_filter

        base += f",fade=t=in:d=0.3,fade=t=out:d=0.3:st={duration-0.3},setpts=PTS-STARTPTS[v{i}]"
        filter_parts.append(base)
        concat_v += f"[v{i}]"

        # Audio
        audio_path = scene.get("audio_path", "")
        if _is_valid_audio(audio_path):
            input_args.extend(["-i", audio_path])
            ai = 2 * i + audio_inputs + 1
            filter_parts.append(f"[{ai}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,apad,atrim=0:{duration}[a{i}]")
            audio_inputs += 1
        else:
            filter_parts.append(f"aevalsrc=0:d={duration}:s=44100[a{i}]")

        concat_a += f"[a{i}]"

    concat_v += f"concat=n={len(scenes)}:v=1:a=0[v]"
    concat_a += f"concat=n={len(scenes)}:v=0:a=1[a]"

    filter_complex = ";".join(filter_parts) + ";" + concat_v + ";" + concat_a

    cmd = ["ffmpeg", "-y"] + input_args + ["-filter_complex", filter_complex]

    # BGM
    if _is_valid_audio(bgm_path):
        cmd.extend(["-i", bgm_path])
        bi = len(input_args) // 2
        cmd.extend([
            "-filter_complex",
            f"{filter_complex};"
            f"[a]volume=1.0[amain];[{bi}:a]volume=0.18,aloop=loop=-1:size=2e9[abgm];"
            f"[amain][abgm]amix=inputs=2:duration=shortest[aout]",
            "-map", "[v]", "-map", "[aout]",
        ])
    else:
        cmd.extend(["-map", "[v]", "-map", "[a]"])

    cmd.extend([
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", str(fps), output_path,
    ])

    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return output_path
