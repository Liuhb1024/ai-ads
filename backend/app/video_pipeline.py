"""Video generation pipeline — turns ad analysis into a 45-second narrated video.

Pipeline:
  1. Script generation (Agnes text model) — analysis JSON → 7-scene storyboard
  2. Visual assets (Agnes image + matplotlib + Pillow) — AI illustrations + chart + text cards
  3. Audio generation (Edge TTS + Pixabay) — narration + BGM
  4. Video composition (MoviePy) — combine all assets into H.264 MP4
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_EXPORTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "exports"
_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

STORYBOARD_SYSTEM = """你是一位专业的短视频内容策划师。你的任务是将广告分析结果转化为45秒横屏视频的分镜脚本。

输出以下JSON格式（7个场景，总时长约45秒）：

{
  "scenes": [
    {
      "scene": 1,
      "duration": 5.0,
      "visual_prompt": "英文，AI生图提示词，画面是概念插图风格，干净简约，无文字，适合横屏",
      "narration": "场景旁白，口语化，有吸引力",
      "overlay_text": "画面大标题，5-15字，尖锐有力"
    },
    ...
  ],
  "title": "视频标题",
  "bgm_mood": "背景音乐情绪关键词"
}

分镜节奏要求：
- 场景1（钩子，5秒）：用反常识结论抓住注意力，画面要有视觉冲击
- 场景2（策略，7秒）：揭示广告的Hook类型和策略
- 场景3（人群，7秒）：目标用户画像和痛点
- 场景4（创意，7秒）：创意亮点分析
- 场景5（信任，6秒）：可信度判断
- 场景6（评分，7秒）：评分结果展示
- 场景7（金句，6秒）：一句话带走

重要规则：
1. 不要提及任何具体的品牌名/产品名（避免版权），用"这个品牌""这款产品"代替
2. 不要说教，要有观点和态度
3. narration 要口语化，像在跟朋友聊天
4. visual_prompt 只用英文，描述画面而非文字
5. 每个场景的 duration 加起来约 45 秒
6. 用中文输出所有字段（visual_prompt除外）"""


async def run_video_pipeline(ad_record: dict, analysis: dict) -> dict[str, Any]:
    """Run the full video generation pipeline.

    Args:
        ad_record: Database row dict with id, brand_name, product_name, industry, platform.
        analysis: Parsed analysis_json dict from the ad.

    Returns:
        {"video_path": str, "status": "completed" | "failed", "error": str | None}
    """
    ad_id = ad_record.get("id", "unknown")
    output_dir = os.path.join(str(_EXPORTS_DIR), ad_id, "video")
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Step 1: Generate storyboard
        logger.info(f"[video:{ad_id}] Step 1/4: Generating storyboard...")
        storyboard = await _generate_storyboard(analysis, ad_record)
        if "error" in storyboard:
            return {"status": "failed", "error": storyboard["error"], "video_path": ""}

        scenes = storyboard.get("scenes", [])
        if len(scenes) < 3:
            # Fallback: generate a basic storyboard
            scenes = _fallback_storyboard(analysis, ad_record)

        # Step 2: Generate visual assets (parallel)
        logger.info(f"[video:{ad_id}] Step 2/4: Generating visual assets...")
        images = await _generate_visuals(scenes, analysis, output_dir)

        # Step 3: Generate audio (parallel)
        logger.info(f"[video:{ad_id}] Step 3/4: Generating audio...")
        scenes, bgm_path = await _generate_audio(scenes, output_dir)

        # Step 4: Render video
        logger.info(f"[video:{ad_id}] Step 4/4: Rendering video...")
        video_path = await _render_video(scenes, images, bgm_path, output_dir, ad_id)

        return {"video_path": video_path, "status": "completed", "error": None}

    except Exception as exc:
        logger.error(f"[video:{ad_id}] Pipeline failed: {exc}")
        return {"status": "failed", "error": str(exc), "video_path": ""}


# ═══════════════════════════════════════════════════════════
# Step 1: Storyboard Generation
# ═══════════════════════════════════════════════════════════

async def _generate_storyboard(analysis: dict, ad_record: dict) -> dict:
    """Generate a 7-scene storyboard using Agnes text model."""
    from .agnesium_client import chat_completion, is_configured

    if not is_configured():
        return _fallback_storyboard(analysis, ad_record)

    context = _build_analysis_context(analysis, ad_record)

    try:
        result = await chat_completion(
            system=STORYBOARD_SYSTEM,
            user=f"以下是广告分析数据，请据此生成45秒分镜脚本：\n\n{context}",
            json_mode=True,
            max_tokens=4096,
        )
        if "_error" in result or "_raw" in result:
            return {"error": result.get("_error", "Storyboard generation failed")}

        scenes = result.get("scenes", [])
        if not scenes:
            return {"error": "No scenes in storyboard"}

        return result

    except Exception as exc:
        return {"error": str(exc)}


def _build_analysis_context(analysis: dict, ad_record: dict) -> str:
    """Build a compact context string from analysis for the storyboard LLM."""
    scoring = analysis.get("scoring", {}) or {}
    ad_strategy = analysis.get("ad_strategy", {}) or {}
    user_insight = analysis.get("user_insight", {}) or {}
    quality_audit = analysis.get("quality_audit", {}) or {}
    final_note = analysis.get("final_note", {}) or {}

    parts = []

    # Industry & platform context
    industry = ad_record.get("industry", "未知")
    platform = ad_record.get("platform", "未知")
    parts.append(f"行业: {industry} | 平台: {platform}")

    # Hook pattern
    hook = (ad_strategy.get("hook_pattern") or {})
    parts.append(f"Hook类型: {hook.get('primary', '未知')} (备选: {hook.get('secondary', '无')})")

    # Scores
    scoring_data = scoring.get("scoring", {}) if isinstance(scoring, dict) else {}
    if scoring_data:
        score_items = []
        for dim, info in scoring_data.items():
            if isinstance(info, dict):
                score_items.append(f"{dim}: {info.get('score', '?')}/5")
        parts.append("评分: " + " | ".join(score_items))

    overall = scoring.get("overall_score", "") if isinstance(scoring, dict) else ""
    tier = scoring.get("tier", "") if isinstance(scoring, dict) else ""
    if overall or tier:
        parts.append(f"总分: {overall} | 等级: {tier}")

    # Strategy highlights
    strategy_highlights = ad_strategy.get("strategy_highlights", []) if isinstance(ad_strategy, dict) else []
    if strategy_highlights:
        parts.append("策略亮点: " + "; ".join(str(str(s) for s in strategy_highlights[:3])))

    # User insight
    if isinstance(user_insight, dict):
        audience = user_insight.get("target_audience", "")
        pain = user_insight.get("core_pain_point", "")
        if audience:
            parts.append(f"目标人群: {audience}")
        if pain:
            parts.append(f"核心痛点: {pain}")

    # Takeaway
    takeaway = final_note.get("one_sentence_takeaway", "") if isinstance(final_note, dict) else ""
    if takeaway:
        parts.append(f"核心洞察: {takeaway}")

    # Trust verdict
    if isinstance(quality_audit, dict):
        verdict = quality_audit.get("verdict", "")
        trust = quality_audit.get("trust_score", "")
        if verdict:
            parts.append(f"可信度判定: {verdict} (信任分: {trust})")

    return "\n".join(parts)


def _fallback_storyboard(analysis: dict, ad_record: dict) -> list[dict]:
    """Generate a basic storyboard without LLM (used when Agnes is not configured or fails)."""
    scoring = analysis.get("scoring", {}) or {}
    ad_strategy = analysis.get("ad_strategy", {}) or {}
    user_insight = analysis.get("user_insight", {}) or {}
    final_note = analysis.get("final_note", {}) or {}

    hook_primary = (ad_strategy.get("hook_pattern") or {}).get("primary", "信息缺口")
    audience = (user_insight.get("target_audience") or "目标消费者") if isinstance(user_insight, dict) else "目标消费者"
    takeaway = (final_note.get("one_sentence_takeaway") or "好创意的背后是对人性的洞察") if isinstance(final_note, dict) else "好创意的背后是对人性的洞察"
    industry = ad_record.get("industry", "消费")
    tier = (scoring.get("tier") or "B") if isinstance(scoring, dict) else "B"

    return [
        {
            "scene": 1, "duration": 5.0,
            "visual_prompt": "dramatic abstract composition with golden light breaking through darkness, minimalist, cinematic, 16:9",
            "narration": f"这条{industry}广告的钩子，用了{hook_primary}，大多数人根本没注意到。",
            "overlay_text": f"这条广告的钩子\n90%的人没看懂",
        },
        {
            "scene": 2, "duration": 7.0,
            "visual_prompt": "magnifying glass over a smartphone screen, digital marketing concept, clean tech style, blue tones, 16:9",
            "narration": f"它不是简单地在卖产品，而是用{hook_primary}的手法，在用户心里种下一个疑问。当这个疑问得不到解答，用户就会往下看。",
            "overlay_text": f"Hook: {hook_primary}",
        },
        {
            "scene": 3, "duration": 7.0,
            "visual_prompt": "diverse crowd of people looking at phones, urban street scene, warm lighting, candid photography style, 16:9",
            "narration": f"它的目标用户是{audience}。为什么选这个人群？因为这群人有一个共同的痛点——信息过载。他们需要的是确定感。",
            "overlay_text": f"目标：{audience}",
        },
        {
            "scene": 4, "duration": 7.0,
            "visual_prompt": "creative lightbulb moment, abstract art, colorful sparks and neural connections, dark background, 16:9",
            "narration": "创意的本质不是炫技，而是在对的时间、用对的方式、把对的话说给对的人。这条广告做到了至少三点。",
            "overlay_text": "创意的本质\n是把对的话说给对的人",
        },
        {
            "scene": 5, "duration": 6.0,
            "visual_prompt": "scale of justice balanced with a heart, symbolic illustration, soft ethereal light, marble texture, 16:9",
            "narration": "它的可信度来自三个方面：信息的真实性、情绪的真诚度、以及品牌的一致性。这三者缺一不可。",
            "overlay_text": "信任的三个支点",
        },
        {
            "scene": 6, "duration": 7.0,
            "visual_prompt": "radar chart hologram floating in dark space, futuristic data visualization, glowing neon edges, 16:9",
            "narration": f"综合评分：等级{tier}。在钩子和转化上表现突出，但在创新性上还有提升空间。这也是大多数行业广告的通病。",
            "overlay_text": f"综合评级：{tier}",
        },
        {
            "scene": 7, "duration": 6.0,
            "visual_prompt": "minimalist typography on clean background, elegant golden ratio composition, morning light, peaceful, 16:9",
            "narration": f"最后，一句话总结：{takeaway}。每天分析一条广告，我们下期见。",
            "overlay_text": takeaway,
        },
    ]


# ═══════════════════════════════════════════════════════════
# Step 2: Visual Asset Generation
# ═══════════════════════════════════════════════════════════

async def _generate_visuals(
    scenes: list[dict],
    analysis: dict,
    output_dir: str,
) -> list[str]:
    """Generate all visual assets in parallel: AI illustrations + radar chart + text cards."""
    from .agnesium_client import generate_image, is_configured

    images: list[str] = [""] * len(scenes)

    # Identify scene types and generate appropriate visuals
    image_tasks = []
    task_indices = []

    for i, scene in enumerate(scenes):
        visual_prompt = scene.get("visual_prompt", "")

        if i == 5 and scene.get("scene") == 6:
            # Scene 6: Radar chart
            images[i] = _generate_radar_chart(analysis, output_dir)
        elif visual_prompt and is_configured():
            # AI illustration
            image_tasks.append(generate_image(visual_prompt, size="1792x1024"))
            task_indices.append(i)
        else:
            # Text card fallback
            images[i] = _generate_text_card(
                scene.get("overlay_text", "广告分析"),
                output_dir,
                f"card_{i:02d}",
            )

    # Run AI image generation in parallel
    if image_tasks:
        results = await asyncio.gather(*image_tasks, return_exceptions=True)
        for idx, result in zip(task_indices, results):
            if isinstance(result, bytes) and len(result) > 100:
                path = os.path.join(output_dir, f"ai_illustration_{idx:02d}.png")
                with open(path, "wb") as f:
                    f.write(result)
                images[idx] = path
            else:
                # Fallback to text card
                images[idx] = _generate_text_card(
                    scenes[idx].get("overlay_text", "广告分析"),
                    output_dir,
                    f"card_{idx:02d}",
                )

    return images


def _generate_radar_chart(analysis: dict, output_dir: str) -> str:
    """Generate a radar/spider chart from scoring data."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return ""

    scoring = analysis.get("scoring", {}) or {}
    scoring_data = scoring.get("scoring", {}) if isinstance(scoring, dict) else {}

    if not scoring_data:
        return ""

    # Dimension names and scores
    dim_labels = {
        "hook": "钩子", "messaging": "信息传递", "conversion": "转化设计",
        "emotion": "情绪调动", "trust": "信任建立",
        "production": "制作水准", "innovation": "创新性",
    }

    labels = []
    values = []
    for key, label in dim_labels.items():
        dim = scoring_data.get(key, {})
        if isinstance(dim, dict):
            score = dim.get("score", 0)
        else:
            score = 0
        labels.append(label)
        values.append(score)

    if not values or max(values) == 0:
        return ""

    # Create radar chart
    n = len(values)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    labels += labels[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor("#0f0f1a")
    ax.set_facecolor("#0f0f1a")

    ax.fill(angles, values, color="#60a5fa", alpha=0.3)
    ax.plot(angles, values, color="#60a5fa", linewidth=2.5)
    ax.scatter(angles[:-1], values[:-1], color="#93c5fd", s=100, zorder=3)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels[:-1], color="white", fontsize=14, fontfamily="sans-serif")
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], color="#888888", fontsize=10)
    ax.spines["polar"].set_color("#333333")
    ax.grid(color="#333333", alpha=0.5)

    # Score labels
    for angle, value, label in zip(angles[:-1], values[:-1], labels[:-1]):
        ax.annotate(
            f"{value}", xy=(angle, value),
            xytext=(5, 5), textcoords="offset points",
            color="white", fontsize=13, fontweight="bold",
        )

    output_path = os.path.join(output_dir, "radar_chart.png")
    plt.savefig(output_path, dpi=100, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


def _generate_text_card(text: str, output_dir: str, name: str) -> str:
    """Generate a text-based card image using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return ""

    width, height = 1920, 1080
    img = Image.new("RGBA", (width, height), (15, 15, 30, 255))
    draw = ImageDraw.Draw(img)

    # Try to load a bold font
    font = None
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    ]
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, 80)
            break
        except (OSError, IOError):
            continue

    if font is None:
        try:
            font = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", 60)
        except (OSError, IOError):
            font = ImageFont.load_default()

    # Draw semi-transparent overlay background
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [(width * 0.15, height * 0.3), (width * 0.85, height * 0.7)],
        fill=(0, 0, 0, 140),
    )
    img = Image.alpha_composite(img, overlay)

    # Draw text
    draw = ImageDraw.Draw(img)
    lines = text.split("\n")
    total_height = len(lines) * 100
    y_start = (height - total_height) / 2

    for i, line in enumerate(lines):
        line_width = font.getbbox(line)[2] if hasattr(font, "getbbox") else font.getsize(line)[0]
        x = (width - line_width) / 2
        y = y_start + i * 100

        # Text shadow
        draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 180))
        # Main text
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

    output_path = os.path.join(output_dir, f"{name}.png")
    img.save(output_path, "PNG")
    return output_path


# ═══════════════════════════════════════════════════════════
# Step 3: Audio Generation (TTS + BGM)
# ═══════════════════════════════════════════════════════════

async def _generate_audio(scenes: list[dict], output_dir: str) -> tuple[list[dict], str]:
    """Generate TTS narration for all scenes + download BGM."""
    from .tts_client import generate_scene_speech
    from .music_client import fetch_bgm

    # TTS for all scenes in parallel
    enriched_scenes = await generate_scene_speech(scenes, output_dir)

    # BGM in parallel with TTS
    bgm_path = os.path.join(output_dir, "bgm.mp3")
    bgm_task = fetch_bgm(bgm_path)

    bgm_result = await bgm_task

    return enriched_scenes, bgm_result or ""


# ═══════════════════════════════════════════════════════════
# Step 4: Video Rendering
# ═══════════════════════════════════════════════════════════

async def _render_video(
    scenes: list[dict],
    images: list[str],
    bgm_path: str,
    output_dir: str,
    ad_id: str,
) -> str:
    """Render the final video using MoviePy."""
    from .video_renderer import render_video

    output_path = os.path.join(output_dir, f"{ad_id}_analysis.mp4")

    # Render in thread pool (MoviePy is CPU-bound and synchronous)
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        render_video,
        scenes,
        images,
        bgm_path,
        output_path,
        1920,
        1080,
        25,
    )
    return result
