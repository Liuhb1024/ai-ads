from __future__ import annotations

import json
import math
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..database import get_db

router = APIRouter(prefix="/api/calibration", tags=["calibration"])

# ── Schemas (inline to keep router self-contained) ─────

DIMENSIONS = [
    ("overall_score", "综合评分"),
    ("hook_score", "钩子"),
    ("messaging_score", "信息传递"),
    ("conversion_score", "转化设计"),
    ("emotion_score", "情绪调动"),
    ("trust_score", "信任建立"),
    ("production_score", "制作水准"),
    ("innovation_score", "创新性"),
]


class ExpertScoreRequest(BaseModel):
    ad_id: str = Field(..., min_length=1)
    expert_id: str = Field(..., min_length=1)
    overall_score: int = Field(ge=0, le=100)
    hook_score: int = Field(ge=1, le=5)
    messaging_score: int = Field(ge=1, le=5)
    conversion_score: int = Field(ge=1, le=5)
    emotion_score: int = Field(ge=1, le=5)
    trust_score: int = Field(ge=1, le=5)
    production_score: int = Field(ge=1, le=5)
    innovation_score: int = Field(ge=1, le=5)
    notes: str | None = None


class CalibrationDimensionResult(BaseModel):
    dimension: str
    label: str
    spearman_rho: float | None
    p_value: float | None
    n_pairs: int
    ai_mean: float
    expert_mean: float
    correlation_label: str


class CalibrationReportResult(BaseModel):
    n_ads: int
    n_experts: int
    overall_spearman_rho: float | None
    overall_p_value: float | None
    per_dimension: list[CalibrationDimensionResult]
    expert_reliability: dict[str, float | None]
    tier_agreement: float | None
    created_at: str


# ── Statistics: Spearman's rank correlation ────────────


def _rankdata(values: list[float]) -> list[float]:
    """Assign average ranks with tie handling (pure Python)."""
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    n = len(indexed)
    while i < n:
        j = i
        while j < n and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j - 1) / 2.0 + 1  # +1 for 1-based ranks
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def _spearman_rho(xs: list[float], ys: list[float]) -> tuple[float | None, float | None]:
    """Compute Spearman's rank correlation coefficient and approximate p-value."""
    n = len(xs)
    if n < 3:
        return None, None
    if len(set(xs)) <= 1 or len(set(ys)) <= 1:
        return None, None  # undefined (zero variance)

    rx = _rankdata(xs)
    ry = _rankdata(ys)

    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    rho = 1.0 - (6.0 * d2) / (n * (n * n - 1))

    # Approximate p-value: t = rho * sqrt((n-2)/(1-rho^2))
    if abs(rho) >= 1.0:
        p = 0.0
    else:
        t_stat = rho * math.sqrt((n - 2) / (1 - rho * rho))
        # Student's t CDF via regularized incomplete beta approximation
        df = n - 2
        x = df / (df + t_stat * t_stat)
        # Regularized incomplete beta for (df/2, 1/2) via series expansion
        p_half = _reg_beta(x, df / 2.0, 0.5)
        p = 2.0 * min(p_half, 1.0 - p_half)
        if p > 1.0:
            p = 1.0

    return rho, p


def _reg_beta(x: float, a: float, b: float, steps: int = 200) -> float:
    """Approximate regularized incomplete beta function I_x(a,b) via continued fraction."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0

    ln_beta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)

    def _cf(x_inner, a_inner, b_inner, ln_beta_inner):
        iters = 200
        eps = 1e-12
        d = 0.0
        c = 1.0
        f = 1.0

        m2 = 0
        for m in range(iters):
            if m == 0:
                num = 1.0
                den = 1.0
            elif m % 2 == 1:
                j = (m - 1) // 2
                num = (a_inner + j) * (a_inner + b_inner + j) * x_inner
                den = (a_inner + 2 * j) * (a_inner + 2 * j + 1)
                if m > 1:
                    num = -num
            else:
                j = m // 2 - 1
                num = j * (b_inner - j) * x_inner
                den = (a_inner + 2 * j) * (a_inner + 2 * j - 1)

            d = den + num * d
            if abs(d) < eps:
                d = eps if d >= 0 else -eps
            c = den + num / c
            if abs(c) < eps:
                c = eps if c >= 0 else -eps
            d = 1.0 / d
            delta = c * d
            f *= delta
            if abs(delta - 1.0) < eps:
                break

        return math.exp(a_inner * math.log(x_inner) + b_inner * math.log(1.0 - x_inner) - ln_beta_inner) / a_inner * f

    return _cf(x, a, b, ln_beta)


def _correlation_label(rho: float | None) -> str:
    if rho is None:
        return "数据不足"
    r = abs(rho)
    if r >= 0.7:
        return "强相关"
    if r >= 0.4:
        return "中等相关"
    if r >= 0.2:
        return "弱相关"
    return "可忽略"


def _ai_tier(score: float) -> str:
    if score >= 80:
        return "S"
    if score >= 65:
        return "A"
    if score >= 50:
        return "B"
    if score >= 35:
        return "C"
    return "D"


def _expert_tier(score: float) -> str:
    # Map 0-100 expert overall score to S/A/B/C/D
    if score >= 80:
        return "S"
    if score >= 65:
        return "A"
    if score >= 50:
        return "B"
    if score >= 35:
        return "C"
    return "D"


# ── Endpoints ──────────────────────────────────────────


@router.post("/scores")
async def submit_score(req: ExpertScoreRequest, db=Depends(get_db)):
    cursor = await db.execute("SELECT status, analysis_json FROM ads WHERE id = ?", (req.ad_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(404, "广告不存在")
    if row["status"] != "completed":
        raise HTTPException(400, "广告尚未分析完成")

    try:
        await db.execute(
            """INSERT OR REPLACE INTO expert_scores
               (ad_id, expert_id, overall_score, hook_score, messaging_score,
                conversion_score, emotion_score, trust_score, production_score,
                innovation_score, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                req.ad_id, req.expert_id, req.overall_score, req.hook_score, req.messaging_score,
                req.conversion_score, req.emotion_score, req.trust_score, req.production_score,
                req.innovation_score, req.notes,
            ),
        )
        await db.commit()
    except Exception as e:
        raise HTTPException(400, f"提交失败: {e}")

    return {"ad_id": req.ad_id, "expert_id": req.expert_id, "status": "saved"}


@router.get("/scores")
async def list_scores(expert_id: str = "", db=Depends(get_db)):
    if expert_id:
        cursor = await db.execute(
            "SELECT * FROM expert_scores WHERE expert_id = ? ORDER BY created_at DESC",
            (expert_id,),
        )
    else:
        cursor = await db.execute("SELECT * FROM expert_scores ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return {"scores": [dict(r) for r in rows], "count": len(rows)}


@router.get("/report")
async def calibration_report(db=Depends(get_db)):
    from datetime import datetime

    cursor = await db.execute("SELECT * FROM expert_scores ORDER BY ad_id, expert_id")
    rows = await cursor.fetchall()
    if not rows:
        return CalibrationReportResult(
            n_ads=0, n_experts=0, overall_spearman_rho=None, overall_p_value=None,
            per_dimension=[], expert_reliability={}, tier_agreement=None,
            created_at=datetime.utcnow().isoformat(),
        )

    # Group scores by ad_id
    ad_scores: dict[str, list[dict]] = {}
    for r in rows:
        ad_scores.setdefault(r["ad_id"], []).append(dict(r))

    expert_ids = sorted({r["expert_id"] for r in rows})

    # Per-dimension correlation
    dim_pairs: dict[str, list[tuple[float, float]]] = {key: [] for key, _ in DIMENSIONS}
    tier_agreements: list[bool] = []

    for ad_id, scores in ad_scores.items():
        ad_analysis = {}
        cursor = await db.execute("SELECT analysis_json FROM ads WHERE id = ?", (ad_id,))
        ad_row = await cursor.fetchone()
        if ad_row and ad_row["analysis_json"]:
            try:
                ad_analysis = json.loads(ad_row["analysis_json"])
            except (json.JSONDecodeError, TypeError):
                pass

        scoring_blob = (ad_analysis.get("scoring") or {}) if isinstance(ad_analysis, dict) else {}
        ai_scoring = scoring_blob.get("scoring", scoring_blob) if isinstance(scoring_blob, dict) else {}
        ai_overall = float(ai_scoring.get("overall_score", 0)) if isinstance(ai_scoring, dict) else 0.0

        for s in scores:
            # Overall score
            dim_pairs["overall_score"].append((ai_overall, float(s.get("overall_score", 0))))
            # Dimension scores: AI uses 1-5, expert also uses 1-5
            dim_map = {
                "hook_score": "hook",
                "messaging_score": "messaging",
                "conversion_score": "conversion",
                "emotion_score": "emotion",
                "trust_score": "trust",
                "production_score": "production",
                "innovation_score": "innovation",
            }
            for dim_key, ai_key in dim_map.items():
                ai_dim_score = 0.0
                if isinstance(ai_scoring, dict):
                    cat = ai_scoring.get(ai_key, {})
                    if isinstance(cat, dict):
                        scores_in_cat = [float(v) for v in cat.values() if isinstance(v, (int, float))]
                        ai_dim_score = sum(scores_in_cat) / len(scores_in_cat) if scores_in_cat else 0.0
                dim_pairs[dim_key].append((ai_dim_score, float(s.get(dim_key, 0))))

            # Tier agreement
            ai_tier = _ai_tier(ai_overall)
            expert_tier = _expert_tier(float(s.get("overall_score", 0)))
            tier_agreements.append(ai_tier == expert_tier)

    # Compute per-dimension Spearman ρ
    per_dim = []
    for dim_key, dim_label in DIMENSIONS:
        pairs = dim_pairs.get(dim_key, [])
        if pairs and len(pairs) >= 3:
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            rho, p = _spearman_rho(xs, ys)
            ai_mean = sum(xs) / len(xs)
            expert_mean = sum(ys) / len(ys)
        else:
            rho, p, ai_mean, expert_mean = None, None, 0.0, 0.0
        per_dim.append(CalibrationDimensionResult(
            dimension=dim_key, label=dim_label,
            spearman_rho=rho, p_value=p, n_pairs=len(pairs) if pairs else 0,
            ai_mean=round(ai_mean, 2), expert_mean=round(expert_mean, 2),
            correlation_label=_correlation_label(rho),
        ))

    # Overall Spearman ρ
    overall_pairs = dim_pairs.get("overall_score", [])
    if overall_pairs and len(overall_pairs) >= 3:
        overall_rho, overall_p = _spearman_rho(
            [p[0] for p in overall_pairs], [p[1] for p in overall_pairs]
        )
    else:
        overall_rho, overall_p = None, None

    # Expert inter-rater reliability (average pairwise correlation)
    expert_reliability: dict[str, float | None] = {}
    if len(expert_ids) >= 2:
        for eid in expert_ids:
            e_scores = [s for ad_s in ad_scores.values() for s in ad_s if s["expert_id"] == eid]
            others = [s for ad_s in ad_scores.values() for s in ad_s if s["expert_id"] != eid]
            if len(e_scores) >= 2 and len(others) >= 2:
                # Pair this expert's scores with average of others per ad
                xs, ys = [], []
                for ad_id in ad_scores:
                    my_s = [s for s in ad_scores[ad_id] if s["expert_id"] == eid]
                    other_s = [s for s in ad_scores[ad_id] if s["expert_id"] != eid]
                    if my_s and other_s:
                        xs.append(float(my_s[0]["overall_score"]))
                        ys.append(sum(float(s["overall_score"]) for s in other_s) / len(other_s))
                if len(xs) >= 3:
                    r, _ = _spearman_rho(xs, ys)
                    expert_reliability[eid] = r
                else:
                    expert_reliability[eid] = None
            else:
                expert_reliability[eid] = None

    tier_agreement_pct = sum(1 for t in tier_agreements if t) / len(tier_agreements) if tier_agreements else None

    return CalibrationReportResult(
        n_ads=len(ad_scores),
        n_experts=len(expert_ids),
        overall_spearman_rho=overall_rho,
        overall_p_value=overall_p,
        per_dimension=per_dim,
        expert_reliability=expert_reliability,
        tier_agreement=tier_agreement_pct,
        created_at=datetime.utcnow().isoformat(),
    )
