from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import aiosqlite

from .agent_pipeline import run_agent_pipeline
from .database import DB_PATH
from .llm_client import chat_completion, is_configured
from .publishing_pipeline import generate_publishing_output
from .reporting import build_report_markdown
from services.link_parser import parse_link
from services.media_pipeline import analyze_video


STAGE_MESSAGES = {
    "resolving": "正在识别平台分享链接",
    "media": "正在下载视频并提取语音与关键画面",
    "identifying": "正在识别品牌、产品和行业",
    "needs_confirmation": "需要确认少量关键信息",
    "analyzing": "正在进行广告策略与用户洞察分析",
    "publishing": "正在生成抖音和小红书发布稿",
    "completed": "分析完成",
    "failed": "处理失败",
}


def critical_missing_fields(metadata: dict) -> list[str]:
    missing = []
    if not str(metadata.get("brand_name") or "").strip():
        missing.append("brand_name")
    if not str(metadata.get("product_name") or "").strip():
        missing.append("product_name")
    industry = str(metadata.get("industry") or "").strip()
    if not industry or industry == "其他":
        missing.append("industry")
    return missing


def normalize_scoring(value: dict) -> dict:
    container = value.get("scoring", value) if isinstance(value, dict) else {}
    if not isinstance(container, dict):
        return {}
    nested = container.get("scoring")
    if isinstance(nested, dict) and isinstance(nested.get("scoring"), dict):
        return nested
    return container


async def run_job(ad_id: str) -> None:
    try:
        row = await _get_job(ad_id)
        await _set_stage(ad_id, "resolving")
        parsed = await parse_link(row["source_url"])
        await _update(
            ad_id,
            source_platform=parsed.platform,
            platform=_legacy_platform(parsed.platform),
            parsed_title=parsed.title,
            parsed_author=parsed.author,
            thumbnail_url=parsed.thumbnail_url,
            source_metadata_json=json.dumps(parsed.raw_metadata, ensure_ascii=False),
            ad_title=parsed.title or row.get("ad_title"),
            ad_copy=parsed.description or row.get("ad_copy"),
        )

        await _set_stage(ad_id, "media")
        media_source = parsed.raw_metadata.get("video_url") or row["source_url"]
        media = await analyze_video(media_source, max_frames=16)
        await _update(
            ad_id,
            media_path=media.video_path or None,
            transcript_json=json.dumps(
                {
                    "full_text": media.transcript,
                    "segments": media.transcript_segments,
                    "language": media.transcript_language,
                    "duration": media.duration,
                },
                ensure_ascii=False,
            ),
            frames_json=json.dumps(media.frames, ensure_ascii=False),
        )

        await _set_stage(ad_id, "identifying")
        identified = await identify_ad_metadata(
            source_text=row["source_text"],
            parsed_title=parsed.title,
            parsed_author=parsed.author,
            description=parsed.description,
            transcript=media.transcript,
        )
        await _update(ad_id, **identified)

        missing = critical_missing_fields(identified)
        if missing:
            await _update(
                ad_id,
                status="needs_confirmation",
                workflow_stage="needs_confirmation",
                progress_message=STAGE_MESSAGES["needs_confirmation"],
                missing_fields_json=json.dumps(missing, ensure_ascii=False),
            )
            return

        await continue_job(ad_id, media=media)
    except Exception as exc:
        await _fail(ad_id, str(exc))


async def continue_job(ad_id: str, media: Any | None = None) -> None:
    try:
        row = await _get_job(ad_id)
        if media is None:
            # Reuse stored media path from run_job to avoid re-downloading the video
            media_source = row.get("media_path") or row["source_url"]
            media = await analyze_video(media_source, max_frames=16)

        await _set_stage(ad_id, "analyzing")
        transcript = _json(row.get("transcript_json")).get("full_text", "")
        ad_input = {
            "ad_title": row.get("parsed_title") or row.get("ad_title"),
            "brand_name": row.get("brand_name"),
            "product_name": row.get("product_name"),
            "industry": row.get("industry"),
            "price_range": row.get("price_range"),
            "ad_copy": transcript or row.get("ad_copy"),
            "scene_description": row.get("scene_description"),
            "screenshot_description": row.get("screenshot_description"),
            "user_context": row.get("user_context"),
            "seen_at": row.get("seen_at"),
            "platform": row.get("source_platform") or row.get("platform"),
        }
        result = await run_agent_pipeline(
            ad_input,
            frames_base64=_vision_frames(media.frame_base64),
            video_path=media.video_path or row.get("media_path") or None,
            video_url=row.get("source_url") or None,
        )
        normalized = normalize_scoring(result)
        if normalized:
            result["scoring"] = normalized

        await _set_stage(ad_id, "publishing")
        publishing = await generate_publishing_output(ad_input, result)
        report_record = {
            **ad_input,
            "id": ad_id,
            "source_platform": row.get("source_platform"),
            "created_at": row.get("created_at"),
        }
        markdown = build_report_markdown(report_record, result, publishing)
        final_note = result.get("final_note")
        if not isinstance(final_note, dict):
            final_note = {}
            result["final_note"] = final_note
        final_note["markdown_content"] = markdown
        await _update(
            ad_id,
            status="completed",
            workflow_stage="completed",
            progress_message=STAGE_MESSAGES["completed"],
            analysis_json=json.dumps(result, ensure_ascii=False),
            publishing_json=json.dumps(publishing, ensure_ascii=False),
            missing_fields_json="[]",
            error_message=None,
            failed_stage=None,
        )
    except Exception as exc:
        await _fail(ad_id, str(exc))


async def identify_ad_metadata(
    *,
    source_text: str,
    parsed_title: str,
    parsed_author: str,
    description: str,
    transcript: str,
) -> dict[str, str]:
    context = "\n".join(part for part in [source_text, parsed_title, description, transcript[:6000]] if part)
    if is_configured():
        result = await chat_completion(
            system=(
                "从广告素材中识别关键信息，输出严格JSON："
                '{"brand_name":"","product_name":"","industry":""}。'
                "industry 只能是 美妆/食品/3C/教育/电商/金融/游戏/其他。"
                "只在证据充分时填写，不要把账号昵称机械当品牌。"
            ),
            user=context,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        if isinstance(result, dict) and not result.get("_error"):
            return {
                "brand_name": str(result.get("brand_name") or "").strip(),
                "product_name": str(result.get("product_name") or "").strip(),
                "industry": str(result.get("industry") or "其他").strip(),
            }

    hashtags = [item.strip() for item in source_text.split("#")[1:] if item.strip()]
    brand = parsed_author.strip() if parsed_author and "用户" not in parsed_author else ""
    product = hashtags[0].split()[0] if hashtags else ""
    return {"brand_name": brand, "product_name": product, "industry": "其他"}


async def _get_job(ad_id: str) -> dict:
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
        row = await cursor.fetchone()
        if not row:
            raise ValueError("分析任务不存在")
        return dict(row)


async def _set_stage(ad_id: str, stage: str) -> None:
    await _update(
        ad_id,
        status="analyzing",
        workflow_stage=stage,
        progress_message=STAGE_MESSAGES[stage],
        failed_stage=None,
        error_message=None,
    )


async def _fail(ad_id: str, message: str) -> None:
    row = await _get_job(ad_id)
    await _update(
        ad_id,
        status="failed",
        failed_stage=row.get("workflow_stage"),
        workflow_stage="failed",
        progress_message=STAGE_MESSAGES["failed"],
        error_message=message[:2000],
    )


async def _update(ad_id: str, **values: Any) -> None:
    if not values:
        return
    values["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    assignments = ", ".join(f"{key} = ?" for key in values)
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute(
            f"UPDATE ads SET {assignments} WHERE id = ?",
            (*values.values(), ad_id),
        )
        await db.commit()


def _vision_frames(frames: list[dict]) -> list[dict]:
    return [
        {"base64": item["base64"], "mime": item.get("mime_type", "image/jpeg")}
        for item in frames
        if item.get("base64")
    ]


def _legacy_platform(platform: str) -> str:
    return platform if platform in {"抖音", "小红书", "视频号", "快手"} else "其他"


def _json(value: str | None) -> dict:
    try:
        return json.loads(value or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
