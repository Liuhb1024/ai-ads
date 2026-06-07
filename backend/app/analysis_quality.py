from __future__ import annotations

from copy import deepcopy
from typing import Any


CLAIM_TYPES = {"observed", "inferred", "hypothesis"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}


def normalize_evidence_ledger(material: dict[str, Any]) -> list[dict[str, Any]]:
    raw_items = material.get("evidence_ledger", []) if isinstance(material, dict) else []
    if not isinstance(raw_items, list):
        return []

    ledger: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        observation = str(raw.get("observation") or raw.get("fact") or "").strip()
        if not observation:
            continue
        ledger.append(
            {
                "id": f"E{len(ledger) + 1:03d}",
                "timestamp": str(raw.get("timestamp") or "时间未知").strip(),
                "modality": str(raw.get("modality") or "unknown").strip().lower(),
                "observation": observation,
                "quote": str(raw.get("quote") or "").strip(),
                "confidence": _confidence(raw.get("confidence")),
            }
        )
    return ledger


def apply_quality_gate(
    section: dict[str, Any],
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    result = deepcopy(section) if isinstance(section, dict) else {}
    valid_ids = {str(item.get("id")) for item in evidence}
    raw_claims = result.get("claims", [])
    if not isinstance(raw_claims, list):
        raw_claims = []

    normalized: list[dict[str, Any]] = []
    for raw in raw_claims:
        if isinstance(raw, str):
            raw = {"claim": raw}
        if not isinstance(raw, dict):
            continue
        claim = str(raw.get("claim") or "").strip()
        if not claim:
            continue
        requested_ids = raw.get("evidence_ids", [])
        if not isinstance(requested_ids, list):
            requested_ids = []
        evidence_ids = [
            str(item) for item in requested_ids
            if str(item) in valid_ids
        ]
        claim_type = str(raw.get("claim_type") or "inferred").strip().lower()
        if claim_type not in CLAIM_TYPES:
            claim_type = "inferred"
        confidence = _confidence(raw.get("confidence"))
        support_status = "supported" if evidence_ids else "unsupported"

        if claim_type == "observed" and not evidence_ids:
            claim_type = "hypothesis"
            confidence = "low"
        elif claim_type in {"inferred", "hypothesis"} and evidence_ids:
            support_status = "partially_supported"

        normalized.append(
            {
                "claim": claim,
                "claim_type": claim_type,
                "confidence": confidence,
                "evidence_ids": evidence_ids,
                "support_status": support_status,
                "counterpoint": str(raw.get("counterpoint") or "").strip(),
            }
        )

    result["claims"] = normalized
    return result


def collect_claims(*sections: dict[str, Any]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        value = section.get("claims", [])
        if isinstance(value, list):
            claims.extend(item for item in value if isinstance(item, dict))
    return claims


def normalize_audit(
    audit: dict[str, Any],
    *,
    claims: list[dict[str, Any]],
) -> dict[str, Any]:
    source = audit if isinstance(audit, dict) else {}
    unsupported = [
        str(item).strip()
        for item in source.get("unsupported_claims", [])
        if str(item).strip()
    ] if isinstance(source.get("unsupported_claims", []), list) else []

    local_unsupported = [
        str(item.get("claim") or "").strip()
        for item in claims
        if item.get("support_status") == "unsupported"
        and str(item.get("claim") or "").strip()
    ]
    for claim in local_unsupported:
        if claim not in unsupported:
            unsupported.append(claim)

    valid_ids = {
        str(item.get("claim_id"))
        for item in claims
        if str(item.get("claim_id") or "").strip()
    }
    unsupported_claim_ids = [
        str(item) for item in source.get("unsupported_claim_ids", [])
        if str(item) in valid_ids
    ] if isinstance(source.get("unsupported_claim_ids", []), list) else []
    for item in claims:
        claim_id = str(item.get("claim_id") or "")
        if item.get("support_status") == "unsupported" and claim_id:
            if claim_id not in unsupported_claim_ids:
                unsupported_claim_ids.append(claim_id)

    approved_claim_ids = [
        str(item) for item in source.get("approved_claim_ids", [])
        if str(item) in valid_ids and str(item) not in unsupported_claim_ids
    ] if isinstance(source.get("approved_claim_ids", []), list) else []
    if not approved_claim_ids:
        approved_claim_ids = [
            str(item.get("claim_id"))
            for item in claims
            if item.get("support_status") != "unsupported"
            and str(item.get("claim_id") or "") not in unsupported_claim_ids
        ]

    try:
        model_trust_score = int(float(source.get("trust_score", 0)))
    except (TypeError, ValueError):
        model_trust_score = 0
    model_trust_score = max(0, min(100, model_trust_score))

    contradictions = _string_list(source.get("contradictions"))
    limitations = _string_list(source.get("limitations"))

    # Severity multipliers (inspired by claude-ads Critical ×5.0 system)
    severity = _compute_severity(claims, unsupported_claim_ids, contradictions, limitations)

    if valid_ids:
        rejected_ratio = len(set(unsupported_claim_ids)) / len(valid_ids)
        local_trust_score = round(
            100
            - rejected_ratio * 45
            - min(len(contradictions) * 6 * severity["contradiction_multiplier"], 30)
            - min(len(limitations) * 2 * severity["limitation_multiplier"], 10)
            - severity["hard_penalty"]
        )
    else:
        local_trust_score = 70 - min(len(unsupported) * 10 * severity["unsupported_multiplier"], 60)
    local_trust_score = max(0, min(100, local_trust_score))

    # The model supplies qualitative scrutiny; the deterministic score prevents
    # internally inconsistent outputs such as approving most claims but scoring 0.
    trust_score = max(
        local_trust_score - 15,
        min(model_trust_score, local_trust_score + 10),
    )

    verdict = str(source.get("verdict") or "review").strip().lower()
    if verdict not in {"pass", "review", "reject"}:
        verdict = "review"
    if unsupported:
        trust_score = min(trust_score, 69)
        verdict = "review" if verdict == "pass" else verdict
    if severity["kill_trigger"]:
        trust_score = min(trust_score, 39)
        verdict = "reject"

    return {
        "trust_score": trust_score,
        "model_trust_score": model_trust_score,
        "local_trust_score": local_trust_score,
        "verdict": verdict,
        "unsupported_claims": unsupported,
        "unsupported_claim_ids": unsupported_claim_ids,
        "approved_claim_ids": approved_claim_ids,
        "contradictions": contradictions,
        "limitations": limitations,
        "severity": severity,
        "publication_guidance": str(source.get("publication_guidance") or "").strip(),
    }


def _compute_severity(
    claims: list[dict[str, Any]],
    unsupported_ids: set | list,
    contradictions: list[str],
    limitations: list[str],
) -> dict[str, Any]:
    """Compute severity multipliers, mirroring claude-ads' severity system.

    Returns severity assessment with multipliers and kill triggers.
    """
    unsupported_set = {str(i) for i in unsupported_ids}
    total = len(claims)
    if total == 0:
        return {
            "level": "unknown",
            "contradiction_multiplier": 1,
            "limitation_multiplier": 1,
            "unsupported_multiplier": 1,
            "hard_penalty": 0,
            "kill_trigger": False,
        }

    rejected = sum(1 for c in claims if str(c.get("claim_id", "")) in unsupported_set)
    observed_count = sum(1 for c in claims if c.get("claim_type") == "observed")
    hypothesis_count = sum(1 for c in claims if c.get("claim_type") == "hypothesis")
    low_confidence = sum(1 for c in claims if c.get("confidence") == "low")
    rejected_ratio = rejected / total if total > 0 else 0
    evidence_weakness = (
        (hypothesis_count + low_confidence * 2) / (total * 3)
        if total > 0 else 0
    )

    multiplier = 1
    hard_penalty = 0
    kill_trigger = False

    # Critical (×5.0): >50% rejected or >3 contradictions
    if rejected_ratio > 0.5 or len(contradictions) > 3:
        multiplier = 5
        hard_penalty = 40
        kill_trigger = True
    # Major (×3.0): >30% rejected or >2 contradictions
    elif rejected_ratio > 0.3 or len(contradictions) > 2:
        multiplier = 3
        hard_penalty = 20
    # Moderate (×2.0): >15% rejected or evidence weakness > 0.3
    elif rejected_ratio > 0.15 or evidence_weakness > 0.3:
        multiplier = 2
    # Minor (×1.0): default, no multiplier

    level = (
        "critical" if kill_trigger
        else "major" if multiplier >= 3
        else "moderate" if multiplier >= 2
        else "minor"
    )

    return {
        "level": level,
        "contradiction_multiplier": multiplier,
        "limitation_multiplier": multiplier,
        "unsupported_multiplier": multiplier,
        "hard_penalty": hard_penalty,
        "kill_trigger": kill_trigger,
        "rejected_ratio": round(rejected_ratio, 3),
        "evidence_weakness": round(evidence_weakness, 3),
    }


def publication_claims(
    claims: list[dict[str, Any]],
    audit: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    audit = audit or {}
    unsupported_ids = {
        str(item) for item in audit.get("unsupported_claim_ids", [])
    } if isinstance(audit.get("unsupported_claim_ids", []), list) else set()
    approved_ids = {
        str(item) for item in audit.get("approved_claim_ids", [])
    } if isinstance(audit.get("approved_claim_ids", []), list) else set()
    return [
        item for item in claims
        if item.get("support_status") in {"supported", "partially_supported"}
        and str(item.get("claim_id") or "") not in unsupported_ids
        and (not approved_ids or str(item.get("claim_id") or "") in approved_ids)
    ]


def _confidence(value: Any) -> str:
    normalized = str(value or "low").strip().lower()
    return normalized if normalized in CONFIDENCE_LEVELS else "low"


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
