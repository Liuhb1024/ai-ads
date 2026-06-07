from __future__ import annotations

import asyncio
import json
import aiosqlite
from pathlib import Path
from typing import Any

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ai-ad.db"

_embedder = None
_index = None
_texts: list[str] = []
_ad_ids: list[str] = []
_is_built = False
_build_lock = asyncio.Lock()


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        _embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _embedder


def _ad_search_text(row: dict) -> str:
    parts: list[str] = []
    for key in ("brand_name", "product_name", "industry"):
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val.strip())
    analysis_json = row.get("analysis_json")
    if isinstance(analysis_json, str):
        try:
            analysis = json.loads(analysis_json)
        except (json.JSONDecodeError, TypeError):
            analysis = {}
        takeaway = (analysis.get("final_note") or {}).get("one_sentence_takeaway")
        if isinstance(takeaway, str) and takeaway.strip():
            parts.append(takeaway.strip())
    return " ".join(parts)


def invalidate_index() -> None:
    """Discard the in-memory index so the next search sees current database state."""
    global _index, _texts, _ad_ids, _is_built
    _index = None
    _texts = []
    _ad_ids = []
    _is_built = False


async def build_index() -> bool:
    global _index, _texts, _ad_ids, _is_built
    async with _build_lock:
        if _is_built:
            return True
        return await _build_index_unlocked()


async def _build_index_unlocked() -> bool:
    global _index, _texts, _ad_ids, _is_built
    try:
        async with aiosqlite.connect(str(_DB_PATH)) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """SELECT id, brand_name, product_name, industry, analysis_json
                   FROM ads WHERE status = 'completed'"""
            )
            rows = await cursor.fetchall()
    except Exception:
        return False

    if not rows:
        _index = None
        _texts = []
        _ad_ids = []
        _is_built = True
        return True

    _ad_ids = [row["id"] for row in rows]
    _texts = [_ad_search_text(dict(row)) for row in rows]

    model = _get_embedder()
    embeddings = model.encode(_texts, convert_to_numpy=True, show_progress_bar=False)

    import faiss

    dim = embeddings.shape[1]
    idx = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    idx.add(embeddings)

    _index = idx
    _is_built = True
    return True


async def search(query: str, top_k: int = 20) -> list[dict[str, Any]]:
    if not _is_built:
        built = await build_index()
        if not built:
            return []

    if _index is None or not _ad_ids:
        return []

    model = _get_embedder()
    q_embed = model.encode([query], convert_to_numpy=True, show_progress_bar=False)
    faiss = __import__("faiss")
    faiss.normalize_L2(q_embed)

    scores, indices = _index.search(q_embed, min(top_k, len(_ad_ids)))

    results: list[dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if 0 <= idx < len(_ad_ids):
            results.append({"id": _ad_ids[idx], "score": float(score)})
    return results
