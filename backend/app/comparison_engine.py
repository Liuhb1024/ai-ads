from __future__ import annotations

import json
from typing import Any

from .agent_pipeline import _compact_json
from .llm_client import chat_completion, is_configured

COMPARISON_SYSTEM = """你是一位广告创意对比分析专家。基于两条广告的结构化分析数据，进行客观对比并预测哪条广告可能表现更好。

输出严格 JSON：
{
  "predicted_winner": "A" | "B" | "tie",
  "confidence": "high" | "medium" | "low",
  "key_differences": ["差异1", "差异2", "差异3"],
  "analysis_markdown": "对比分析正文(markdown格式)...",
  "ad_a_strengths": ["优势1", "优势2"],
  "ad_a_weaknesses": ["劣势1"],
  "ad_b_strengths": ["优势1"],
  "ad_b_weaknesses": ["劣势1"],
  "hook_comparison": "钩子对比分析",
  "audience_comparison": "人群匹配对比",
  "trust_comparison": "信任机制对比"
}

对比维度（按重要性排序）：
1. 钩子有效性：前3秒抓注意力能力对比
2. 信息传递清晰度：USP是否被受众快速理解
3. 转化设计：CTA 明确度、紧迫感、门槛高低
4. 情绪精准度：目标情绪是否匹配用户痛点和欲望
5. 信任机制：背书强度、社交证明、数据支撑
6. 制作水准：视觉/音频质量、节奏把控
7. 创新性：是否打破品类套路

分析原则：
- 基于证据而非直觉进行对比
- 明确指出每条广告的具体优势和劣势
- 预测不是确定结论，是概率性判断
- 如果两条广告质量接近或品类不同难以直接对比，降低 confidence
- 中文输出"""


def _extract_scoring(analysis: dict) -> dict[str, Any]:
    scoring = (analysis or {}).get("scoring") or {}
    if isinstance(scoring, dict):
        return scoring.get("scoring", scoring)
    return {}


def _build_comparison_context(ad_a: dict, ad_b: dict) -> dict[str, Any]:
    analysis_a = ad_a.get("analysis_json") or {}
    analysis_b = ad_b.get("analysis_json") or {}
    if isinstance(analysis_a, str):
        analysis_a = json.loads(analysis_a)
    if isinstance(analysis_b, str):
        analysis_b = json.loads(analysis_b)

    def slim(analysis: dict) -> dict[str, Any]:
        return {
            "material_understanding": _compact_json(
                analysis.get("material_understanding") or {}
            ),
            "ad_strategy": _compact_json(analysis.get("ad_strategy") or {}),
            "user_insight": _compact_json(analysis.get("user_insight") or {}),
            "scoring": _extract_scoring(analysis),
        }

    return {
        "ad_a": {
            "brand_name": ad_a.get("brand_name", ""),
            "product_name": ad_a.get("product_name", ""),
            "industry": ad_a.get("industry", ""),
            "platform": ad_a.get("platform", ""),
            "analysis": slim(analysis_a),
        },
        "ad_b": {
            "brand_name": ad_b.get("brand_name", ""),
            "product_name": ad_b.get("product_name", ""),
            "industry": ad_b.get("industry", ""),
            "platform": ad_b.get("platform", ""),
            "analysis": slim(analysis_b),
        },
    }


async def run_comparison(ad_a: dict, ad_b: dict) -> dict[str, Any]:
    if not is_configured():
        return _mock_comparison(ad_a, ad_b)

    context = _build_comparison_context(ad_a, ad_b)
    result = await chat_completion(
        system=COMPARISON_SYSTEM,
        user=json.dumps(context, ensure_ascii=False, indent=2),
        max_tokens=4096,
        response_format={"type": "json_object"},
    )
    if isinstance(result, dict) and not result.get("_error"):
        return result
    return _mock_comparison(ad_a, ad_b)


def _mock_comparison(ad_a: dict, ad_b: dict) -> dict[str, Any]:
    return {
        "predicted_winner": "tie",
        "confidence": "low",
        "key_differences": ["两条广告缺少足够的分析数据，无法进行有意义的对比"],
        "analysis_markdown": "当前为 mock 模式，对比分析需要 LLM 调用。",
        "ad_a_strengths": ["数据不足"],
        "ad_a_weaknesses": ["数据不足"],
        "ad_b_strengths": ["数据不足"],
        "ad_b_weaknesses": ["数据不足"],
        "hook_comparison": "数据不足",
        "audience_comparison": "数据不足",
        "trust_comparison": "数据不足",
    }
