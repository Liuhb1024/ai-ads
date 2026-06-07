from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response

from ..database import get_db
from ..mock_pipeline import run_mock_pipeline
from ..llm_client import is_configured
from ..agent_pipeline import run_agent_pipeline
from ..pdf_export import render_markdown_pdf
from ..reporting import build_report_markdown
from ..schemas import (
    AdCreateRequest,
    AdCreateResponse,
    AdDetail,
    AdSummary,
    ErrorResponse,
    HealthResponse,
    JobCreateRequest,
    JobCreateResponse,
    MetadataConfirmationRequest,
    ParseLinkRequest,
    ParseLinkResponse,
    MediaAnalyzeRequest,
    MediaAnalyzeResponse,
)
from ..share_text import ShareTextError, extract_supported_url
from ..swipe_index import invalidate_index, search as semantic_search
from ..workflow import continue_job, run_job

import sys
from pathlib import Path as _Path

_SERVICES_DIR = _Path(__file__).resolve().parent.parent.parent / "services"
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

from link_parser import parse_link
from link_parser import detect_platform
from media_pipeline import analyze_video

router = APIRouter(prefix="/api", tags=["ads"])

EXPORTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Health ──────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", version="0.3.1", mock_mode=not is_configured())


# ── Link parsing ────────────────────────────────────────

@router.post("/parse-link", response_model=ParseLinkResponse)
async def parse_link_endpoint(req: ParseLinkRequest):
    result = await parse_link(req.url)
    return ParseLinkResponse(
        url=result.url,
        platform=result.platform,
        title=result.title,
        author=result.author,
        description=result.description,
        thumbnail_url=result.thumbnail_url,
        parsed=result.parsed,
        error=result.error,
    )


# ── Media analysis ─────────────────────────────────────

@router.post("/analyze-media", response_model=MediaAnalyzeResponse)
async def analyze_media_endpoint(req: MediaAnalyzeRequest):
    result = await analyze_video(req.url, max_frames=30)
    return MediaAnalyzeResponse(
        url=result.url,
        duration=result.duration,
        transcript=result.transcript,
        transcript_segments=[
            {"start": s["start"], "end": s["end"], "text": s["text"]}
            for s in result.transcript_segments
        ],
        transcript_language=result.transcript_language,
        frame_count=len(result.frames),
        error=result.error,
    )


# ── Create ad record ───────────────────────────────────

@router.post("/jobs", response_model=JobCreateResponse, status_code=202)
async def create_job(
    req: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
):
    try:
        source_url = extract_supported_url(req.share_text)
    except ShareTextError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    ad_id = str(uuid.uuid4())[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_platform = detect_platform(source_url)
    platform = source_platform if source_platform in {"抖音", "小红书", "视频号", "快手"} else "其他"

    await db.execute(
        """INSERT INTO ads (
            id, status, brand_name, industry, platform, source_text, source_url,
            source_platform, workflow_stage, progress_message, created_at, updated_at
        ) VALUES (?, 'analyzing', '', '其他', ?, ?, ?, ?, 'resolving', ?, ?, ?)""",
        (
            ad_id,
            platform,
            req.share_text,
            source_url,
            source_platform,
            "正在识别平台分享链接",
            now,
            now,
        ),
    )
    await db.commit()
    background_tasks.add_task(run_job, ad_id)
    return JobCreateResponse(
        id=ad_id,
        status="analyzing",
        stage="resolving",
        next_url=f"/jobs/{ad_id}",
    )


@router.get("/jobs/{ad_id}")
async def get_job(ad_id: str, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    record = dict(row)
    analysis = _load_json(record.get("analysis_json"), None)
    publishing = _load_json(record.get("publishing_json"), None)
    if record.get("status") == "completed" and isinstance(analysis, dict):
        final_note = analysis.get("final_note")
        if not isinstance(final_note, dict):
            final_note = {}
            analysis["final_note"] = final_note
        final_note["markdown_content"] = build_report_markdown(
            record,
            analysis,
            publishing or {},
        )
    return {
        "id": record["id"],
        "status": record["status"],
        "stage": record.get("workflow_stage") or record["status"],
        "progress_message": record.get("progress_message") or "",
        "source_url": record.get("source_url"),
        "source_platform": record.get("source_platform") or record.get("platform"),
        "parsed_title": record.get("parsed_title") or record.get("ad_title"),
        "parsed_author": record.get("parsed_author"),
        "thumbnail_url": record.get("thumbnail_url"),
        "brand_name": record.get("brand_name"),
        "product_name": record.get("product_name"),
        "industry": record.get("industry"),
        "missing_fields": _load_json(record.get("missing_fields_json"), []),
        "analysis": analysis,
        "publishing": publishing,
        "error_message": record.get("error_message"),
        "failed_stage": record.get("failed_stage"),
        "video_status": record.get("video_status", ""),
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
    }


@router.patch("/jobs/{ad_id}/metadata")
async def confirm_job_metadata(
    ad_id: str,
    req: MetadataConfirmationRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
):
    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="分析任务不存在")

    values = {
        "brand_name": req.brand_name or row["brand_name"],
        "product_name": req.product_name or row["product_name"],
        "industry": req.industry.value if req.industry else row["industry"],
    }
    missing = [
        key for key, value in values.items()
        if not value or (key == "industry" and value == "其他")
    ]
    if missing:
        raise HTTPException(status_code=422, detail=f"请补充：{', '.join(missing)}")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await db.execute(
        """UPDATE ads SET brand_name = ?, product_name = ?, industry = ?,
           status = 'analyzing', workflow_stage = 'analyzing',
           progress_message = '正在进行广告策略与用户洞察分析',
           missing_fields_json = '[]', updated_at = ? WHERE id = ?""",
        (*values.values(), now, ad_id),
    )
    await db.commit()
    background_tasks.add_task(continue_job, ad_id)
    return {"id": ad_id, "status": "analyzing", "stage": "analyzing"}


@router.post("/jobs/{ad_id}/retry", status_code=202)
async def retry_job(ad_id: str, background_tasks: BackgroundTasks, db=Depends(get_db)):
    cursor = await db.execute("SELECT id FROM ads WHERE id = ?", (ad_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="分析任务不存在")
    await db.execute(
        """UPDATE ads SET status = 'analyzing', workflow_stage = 'resolving',
           progress_message = '正在重新处理', error_message = NULL, failed_stage = NULL
           WHERE id = ?""",
        (ad_id,),
    )
    await db.commit()
    background_tasks.add_task(run_job, ad_id)
    return {"id": ad_id, "status": "analyzing", "stage": "resolving"}

@router.post("/ads", response_model=AdCreateResponse, status_code=201)
async def create_ad(req: AdCreateRequest, db=Depends(get_db)):
    ad_id = str(uuid.uuid4())[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    await db.execute(
        """INSERT INTO ads (id, status, ad_title, brand_name, product_name,
           industry, price_range, ad_copy, scene_description,
           screenshot_description, user_context, seen_at, platform,
           created_at, updated_at)
           VALUES (?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            ad_id,
            req.ad_title,
            req.brand_name,
            req.product_name,
            req.industry.value,
            req.price_range.value if req.price_range else None,
            req.ad_copy,
            req.scene_description,
            req.screenshot_description,
            req.user_context,
            req.seen_at,
            req.platform.value,
            now,
            now,
        ),
    )
    await db.commit()

    return AdCreateResponse(id=ad_id, status="pending", created_at=now)


# ── List ads ────────────────────────────────────────────

@router.get("/ads")
async def list_ads(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db=Depends(get_db),
):
    cursor = await db.execute(
        "SELECT id, brand_name, product_name, industry, platform, status, created_at, analysis_json FROM ads ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = await cursor.fetchall()

    # Count total
    count_cursor = await db.execute("SELECT COUNT(*) FROM ads")
    total = (await count_cursor.fetchone())[0]

    items = []
    for row in rows:
        takeaway = None
        if row["analysis_json"]:
            try:
                analysis = json.loads(row["analysis_json"])
                takeaway = (analysis.get("final_note") or {}).get("one_sentence_takeaway")
            except (json.JSONDecodeError, TypeError):
                pass

        items.append(
            AdSummary(
                id=row["id"],
                brand_name=row["brand_name"],
                product_name=row["product_name"],
                industry=row["industry"],
                platform=row["platform"],
                status=row["status"],
                created_at=row["created_at"],
                one_sentence_takeaway=takeaway,
            )
        )

    return {"total": total, "limit": limit, "offset": offset, "items": [item.model_dump() for item in items]}


# ── Semantic search ───────────────────────────────────

@router.get("/ads/search")
async def search_ads(
    q: str = Query(default="", min_length=1),
    top_k: int = Query(default=20, ge=1, le=50),
    db=Depends(get_db),
):
    """Semantic search over completed ads using sentence-transformers embeddings + FAISS."""
    results = await semantic_search(q, top_k)
    if not results:
        return {"items": [], "total": 0, "query": q}

    result_ids = [str(result["id"]) for result in results]
    score_by_id = {r["id"]: r["score"] for r in results}
    placeholders = ", ".join("?" for _ in result_ids)

    cursor = await db.execute(
        f"""SELECT id, brand_name, product_name, industry, platform, status, created_at, analysis_json
            FROM ads WHERE id IN ({placeholders})""",
        result_ids,
    )
    rows = await cursor.fetchall()

    items = []
    for row in rows:
        takeaway = None
        if row["analysis_json"]:
            try:
                analysis = json.loads(row["analysis_json"])
                takeaway = (analysis.get("final_note") or {}).get("one_sentence_takeaway")
            except (json.JSONDecodeError, TypeError):
                pass
        item = AdSummary(
            id=row["id"],
            brand_name=row["brand_name"],
            product_name=row["product_name"],
            industry=row["industry"],
            platform=row["platform"],
            status=row["status"],
            created_at=row["created_at"],
            one_sentence_takeaway=takeaway,
        ).model_dump()
        item["_score"] = score_by_id.get(row["id"], 0.0)
        items.append(item)

    items.sort(key=lambda x: x["_score"], reverse=True)
    return {"items": items, "total": len(items), "query": q}


# ── Get ad detail ───────────────────────────────────────

@router.get("/ads/{ad_id}", response_model=AdDetail)
async def get_ad(ad_id: str, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="分析记录不存在")

    analysis = None
    if row["analysis_json"]:
        try:
            analysis = json.loads(row["analysis_json"])
        except (json.JSONDecodeError, TypeError):
            pass

    return AdDetail(
        id=row["id"],
        status=row["status"],
        ad_title=row["ad_title"],
        brand_name=row["brand_name"],
        product_name=row["product_name"],
        industry=row["industry"],
        price_range=row["price_range"],
        ad_copy=row["ad_copy"],
        scene_description=row["scene_description"],
        screenshot_description=row["screenshot_description"],
        user_context=row["user_context"],
        seen_at=row["seen_at"],
        platform=row["platform"],
        analysis=analysis,
        error_message=row["error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ── Trigger analysis ───────────────────────────────────

async def _run_legacy_analysis(ad_id: str) -> None:
    """Background task: run agent pipeline for manually created ads."""
    import aiosqlite

    from ..database import DB_PATH as _DB_PATH

    async with aiosqlite.connect(str(_DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
        row = await cursor.fetchone()
        if not row:
            return

        ad_input = {
            "ad_title": row["ad_title"],
            "brand_name": row["brand_name"],
            "product_name": row["product_name"],
            "industry": row["industry"],
            "price_range": row["price_range"],
            "ad_copy": row["ad_copy"],
            "scene_description": row["scene_description"],
            "screenshot_description": row["screenshot_description"],
            "user_context": row["user_context"],
            "seen_at": row["seen_at"],
            "platform": row["platform"],
        }

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            if is_configured():
                result = await run_agent_pipeline(ad_input)
            else:
                result = run_mock_pipeline(ad_input)

            await db.execute(
                "UPDATE ads SET status = 'completed', analysis_json = ?, updated_at = ? WHERE id = ?",
                (json.dumps(result, ensure_ascii=False), now, ad_id),
            )
            await db.commit()
            invalidate_index()
        except Exception as exc:
            await db.execute(
                "UPDATE ads SET status = 'failed', error_message = ?, failed_stage = 'analyzing', updated_at = ? WHERE id = ?",
                (str(exc)[:2000], now, ad_id),
            )
            await db.commit()


@router.post("/ads/{ad_id}/analyze", status_code=202)
async def analyze_ad(ad_id: str, background_tasks: BackgroundTasks, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="分析记录不存在")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await db.execute(
        "UPDATE ads SET status = 'analyzing', workflow_stage = 'analyzing', progress_message = '正在进行广告策略与用户洞察分析', updated_at = ? WHERE id = ?",
        (now, ad_id),
    )
    await db.commit()
    background_tasks.add_task(_run_legacy_analysis, ad_id)
    return {"id": ad_id, "status": "analyzing", "stage": "analyzing"}


# ── Get analysis result ─────────────────────────────────

@router.get("/ads/{ad_id}/analysis")
async def get_analysis(ad_id: str, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="分析记录不存在")

    if row["status"] == "pending":
        raise HTTPException(status_code=400, detail="尚未开始分析，请先调用 POST /api/ads/{ad_id}/analyze")

    if row["status"] == "analyzing":
        return {"status": "analyzing", "message": "分析进行中"}

    if row["status"] == "failed":
        return {"status": "failed", "error": row["error_message"]}

    analysis = json.loads(row["analysis_json"]) if row["analysis_json"] else {}
    return {"status": "completed", "analysis": analysis}


# ── Export Markdown ─────────────────────────────────────

@router.get("/jobs/{ad_id}/export.md")
@router.get("/ads/{ad_id}/export.md")
async def export_markdown(ad_id: str, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="分析记录不存在")

    if row["status"] != "completed":
        raise HTTPException(status_code=400, detail="分析尚未完成，无法导出")

    record = dict(row)
    markdown = _build_export_markdown(record)

    # Also save to exports directory
    safe_brand = _safe_filename_part(row["brand_name"] or "unknown")
    date_str = (row["created_at"] or "19700101")[:10].replace("-", "")
    filename = f"ad-insight-{safe_brand}-{date_str}.md"
    filepath = EXPORTS_DIR / filename
    filepath.write_text(markdown, encoding="utf-8")

    safe_filename = f"ad-insight-{ad_id}.md"

    return PlainTextResponse(
        content=markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'},
    )


@router.get("/jobs/{ad_id}/export.pdf")
@router.get("/ads/{ad_id}/export.pdf")
async def export_pdf(ad_id: str, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    if row["status"] != "completed":
        raise HTTPException(status_code=400, detail="分析尚未完成，无法导出")

    record = dict(row)
    markdown = _build_export_markdown(record)
    try:
        pdf = render_markdown_pdf(markdown)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败：{exc}") from exc

    safe_brand = _safe_filename_part(record.get("brand_name") or "unknown")
    date_str = (record.get("created_at") or "19700101")[:10].replace("-", "")
    archive_path = EXPORTS_DIR / f"ad-insight-{safe_brand}-{date_str}.pdf"
    archive_path.write_bytes(pdf)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ad-insight-{ad_id}.pdf"'},
    )


def _build_export_markdown(record: dict) -> str:
    analysis = _load_json(record.get("analysis_json"), {})
    publishing = _load_json(record.get("publishing_json"), {})
    markdown = build_report_markdown(record, analysis, publishing)
    final_note = analysis.get("final_note")
    if isinstance(final_note, dict):
        final_note["markdown_content"] = markdown
    return markdown


def _safe_filename_part(value: str) -> str:
    safe = "".join(
        char if (char.isascii() and char.isalnum()) or char in "_-" else "_"
        for char in value
    )
    return safe.strip("_") or "unknown"


def _load_json(value: str | None, default):
    try:
        return json.loads(value) if value else default
    except (json.JSONDecodeError, TypeError):
        return default


# ── Video generation ──────────────────────────────────────

@router.post("/jobs/{ad_id}/video", status_code=202)
async def generate_video(
    ad_id: str,
    db=Depends(get_db),
):
    """Start video generation for a completed ad analysis."""
    import asyncio
    import traceback
    import logging
    _logger = logging.getLogger("video_api")

    cursor = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    if row["status"] != "completed":
        raise HTTPException(status_code=400, detail="只有已完成的分析才能生成视频")

    # Check video status: prevent duplicate generation
    video_status = row["video_status"] or ""
    if video_status == "generating":
        raise HTTPException(status_code=409, detail="视频正在生成中，请稍后再试")

    analysis = _load_json(row["analysis_json"], {})
    if not analysis:
        raise HTTPException(status_code=400, detail="没有分析数据，无法生成视频")

    # Snapshot row data before connection closes
    ad_record = {
        "id": row["id"],
        "brand_name": row["brand_name"] or "",
        "product_name": row["product_name"] or "",
        "industry": row["industry"] or "",
        "platform": row["platform"] or "",
    }

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await db.execute(
        "UPDATE ads SET video_status = 'generating', video_path = '', updated_at = ? WHERE id = ?",
        (now, ad_id),
    )
    await db.commit()

    from ..video_pipeline import run_video_pipeline
    from ..database import DB_PATH as _DB_PATH

    async def _generate():
        _logger.info(f"[video:{ad_id}] Background task started")
        try:
            import aiosqlite
            result = await run_video_pipeline(ad_record, analysis)
            now2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _logger.info(f"[video:{ad_id}] Pipeline result: {result.get('status')}")
            async with aiosqlite.connect(str(_DB_PATH)) as _db:
                _db.row_factory = aiosqlite.Row
                if result["status"] == "completed":
                    await _db.execute(
                        "UPDATE ads SET video_status = 'completed', video_path = ?, updated_at = ? WHERE id = ?",
                        (result["video_path"], now2, ad_id),
                    )
                else:
                    await _db.execute(
                        "UPDATE ads SET video_status = 'failed', video_path = ?, updated_at = ? WHERE id = ?",
                        (result.get("error", ""), now2, ad_id),
                    )
                await _db.commit()
            _logger.info(f"[video:{ad_id}] DB updated")
        except Exception as exc:
            _logger.error(f"[video:{ad_id}] Background task crashed: {exc}\n{traceback.format_exc()}")
            try:
                import aiosqlite
                async with aiosqlite.connect(str(_DB_PATH)) as _db:
                    await _db.execute(
                        "UPDATE ads SET video_status = 'failed', video_path = ?, updated_at = ? WHERE id = ?",
                        (f"内部错误: {exc}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ad_id),
                    )
                    await _db.commit()
            except Exception:
                _logger.error(f"[video:{ad_id}] Even DB error update failed")

    asyncio.create_task(_generate())

    return {"status": "generating", "video_url": ""}


@router.get("/jobs/{ad_id}/video")
async def get_video_status(ad_id: str, db=Depends(get_db)):
    """Check video generation status."""
    from ..video_pipeline import get_pipeline_progress

    cursor = await db.execute("SELECT video_status, video_path FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="分析任务不存在")

    status = row["video_status"] or ""
    video_url = f"/api/jobs/{ad_id}/video.mp4" if status == "completed" else ""

    result: dict = {
        "status": status,
        "video_url": video_url,
        "error": row["video_path"] if status == "failed" else None,
    }

    if status == "generating":
        progress = get_pipeline_progress(ad_id)
        if progress:
            result["stage"] = progress.get("stage", "")
            result["progress_message"] = progress.get("message", "")
            result["percent"] = progress.get("percent", 0)

    return result


@router.get("/jobs/{ad_id}/video.mp4")
async def download_video(ad_id: str, db=Depends(get_db)):
    """Download the generated video file."""
    import os
    from fastapi.responses import FileResponse

    cursor = await db.execute("SELECT video_status, video_path FROM ads WHERE id = ?", (ad_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    if row["video_status"] != "completed" or not row["video_path"]:
        raise HTTPException(status_code=404, detail="视频尚未生成或生成失败")

    path = row["video_path"]
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    return FileResponse(path, media_type="video/mp4", filename=f"{ad_id}_analysis.mp4")
