from __future__ import annotations

import json
from typing import Any

from .analysis_quality import collect_claims, publication_claims
from .llm_client import chat_completion, is_configured


CANDIDATE_SYSTEM = """你是资深中文内容总编。请基于已审查通过的证据，生成两套角度明显不同、都可直接发布的自媒体方案。

请输出严格 JSON：
{
  "candidates": [
    {
      "candidate_id": "A",
      "concept_name": "编辑概念名",
      "editorial_angle": "核心切口",
      "douyin_article": {
        "title": "24字以内标题",
        "hook": "开头两句",
        "body": "适合抖音图文/作品描述的正文，600-1000字，短段落",
        "cta": "自然的评论互动句",
        "hashtags": ["#广告拆解"]
      },
      "douyin_script": {
        "title": "口播题目",
        "duration_seconds": 75,
        "hook": "前3秒口播",
        "beats": [{"label": "段落名", "script": "可直接念的台词"}],
        "cta": "结尾互动台词",
        "full_script": "完整60-90秒口播稿"
      },
      "xiaohongshu": {
        "titles": ["标题1", "标题2", "标题3"],
        "body": "小红书正文，观点密集、短段落",
        "hashtags": ["#广告观察"],
        "image_card_ideas": ["首图文案", "第二张卡片内容"]
      }
    }
  ]
}

要求：
1. 必须返回 A、B 两套完整候选，结构相同但角度、钩子和叙事推进不能只是换词。
2. A 偏证据拆解与专业判断；B 偏反常识观察或创作者可复用启发。
3. 抖音是主平台，文章和口播必须能直接发布。
4. 观点锋利但不标题党，不编造销量、转化率、投放数据。
5. observed 可以陈述；inferred/hypothesis 必须使用“我的判断是”“更可能”等措辞。
6. 审查中 unsupported_claims 禁止进入成稿。
7. “让用户停留、降低试错、促成下单、提升转化”等效果必须改写为“试图吸引停留、意在降低顾虑、引导下单”，不得写成已发生的因果结果。
8. 价格、功效和体验只能表述为“视频标注/素材宣称/口播描述”，不得当作第三方核验事实。
9. 不写“作为AI”，不输出Markdown代码块，不堆砌营销黑话。"""


JUDGE_SYSTEM = """你是一位独立内容评审。请对两个候选做成对比较，不重写稿件。

输出严格 JSON：
{
  "winner": "A或B",
  "scores": {
    "A": {"credibility": 0, "novelty": 0, "clarity": 0, "platform_fit": 0, "actionability": 0},
    "B": {"credibility": 0, "novelty": 0, "clarity": 0, "platform_fit": 0, "actionability": 0}
  },
  "reason": "100字内说明"
}

每项0-10分。可信度是硬门槛：出现无证据数据、夸大效果或把推断当事实，credibility 不得超过4。不要偏好先出现的候选。"""


async def generate_publishing_output(ad: dict, analysis: dict) -> dict[str, Any]:
    if is_configured():
        context = _publication_context(ad, analysis)
        generated = await chat_completion(
            system=CANDIDATE_SYSTEM,
            user=(
                "请生成两套发布候选。\n\n"
                f"{json.dumps(context, ensure_ascii=False, indent=2)}"
            ),
            max_tokens=8192,
            response_format={"type": "json_object"},
        )
        candidates = generated.get("candidates", []) if isinstance(generated, dict) else []
        if _valid_candidates(candidates):
            forward = await _judge_candidates(candidates)
            reverse = await _judge_candidates(list(reversed(candidates)))
            selected = dict(_select_candidate(candidates, forward, reverse))
            selected["_editorial_meta"] = {
                "selected_candidate": selected.get("candidate_id", "A"),
                "concept_name": selected.get("concept_name", ""),
                "editorial_angle": selected.get("editorial_angle", ""),
                "forward_winner": forward.get("winner"),
                "reverse_winner": reverse.get("winner"),
                "selection_method": "position_balanced_pairwise_judging",
            }
            if _valid_output(selected):
                return selected

    return _fallback_output(ad, analysis)


async def _judge_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    result = await chat_completion(
        system=JUDGE_SYSTEM,
        user=json.dumps(candidates, ensure_ascii=False, indent=2),
        max_tokens=1600,
        response_format={"type": "json_object"},
    )
    return result if isinstance(result, dict) and not result.get("_error") else {}


def _publication_context(ad: dict, analysis: dict) -> dict[str, Any]:
    material = analysis.get("material_understanding") or {}
    claims = collect_claims(
        analysis.get("ad_strategy") or {},
        analysis.get("user_insight") or {},
        analysis.get("macro_context") or {},
    )
    return {
        "ad": ad,
        "evidence_ledger": material.get("evidence_ledger", []),
        "approved_claims": publication_claims(
            claims,
            analysis.get("quality_audit") or {},
        ),
        "quality_audit": analysis.get("quality_audit") or {},
        "scoring": analysis.get("scoring") or {},
        "editorial_metadata": analysis.get("final_note") or {},
    }


def _valid_candidates(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and {str(item.get("candidate_id")) for item in value if isinstance(item, dict)} == {"A", "B"}
        and all(_valid_output(item) for item in value)
    )


def _select_candidate(
    candidates: list[dict[str, Any]],
    forward: dict[str, Any],
    reverse: dict[str, Any],
) -> dict[str, Any]:
    by_id = {str(item.get("candidate_id")): item for item in candidates}
    forward_winner = str(forward.get("winner") or "")
    reverse_winner = str(reverse.get("winner") or "")
    if forward_winner == reverse_winner and forward_winner in by_id:
        return by_id[forward_winner]

    totals = {"A": 0.0, "B": 0.0}
    for judging in (forward, reverse):
        scores = judging.get("scores", {}) if isinstance(judging, dict) else {}
        for candidate_id in totals:
            candidate_scores = scores.get(candidate_id, {}) if isinstance(scores, dict) else {}
            if isinstance(candidate_scores, dict):
                totals[candidate_id] += sum(
                    float(value)
                    for value in candidate_scores.values()
                    if isinstance(value, (int, float))
                )
    winner = max(totals, key=lambda item: (totals[item], item == "A"))
    return by_id.get(winner) or candidates[0]


def _valid_output(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("douyin_article"), dict)
        and isinstance(value.get("douyin_script"), dict)
        and isinstance(value.get("xiaohongshu"), dict)
    )


def _fallback_output(ad: dict, analysis: dict) -> dict[str, Any]:
    brand = ad.get("brand_name") or "这条广告"
    product = ad.get("product_name") or "这款产品"
    takeaway = (analysis.get("final_note") or {}).get("one_sentence_takeaway") or (
        f"{brand}没有只卖{product}，而是在出售一种更容易被记住的消费理由。"
    )
    body = (
        f"最近看到一条{brand}的广告，我觉得值得拆一下。\n\n"
        f"先说结论：{takeaway}\n\n"
        "真正有效的地方，不只是产品露出，而是它先建立了一个具体情境，再把产品放进解决方案里。"
        "用户记住的不是参数本身，而是“为什么现在需要它”。\n\n"
        "我的判断是，这种结构最值得复用的部分，是先用可感知的问题抓注意力，再给出足够具体的证明，"
        "最后才进入行动引导。缺少真实投放数据，因此这里讨论的是创意结构，而不是转化效果。\n\n"
        "做同类内容时，可以借结构，但不要照搬结论：先找到用户正在经历的场景，再决定产品应该在第几秒出现。"
    )
    script = (
        f"最近看到{brand}这条广告，我发现它卖的可能不只是{product}。"
        f"{takeaway} "
        "它先把用户拉进一个熟悉的消费场景，再给出产品作为解决办法。"
        "这里最值得借鉴的不是一句文案，而是顺序：先说用户的问题，再给证明，最后才做转化。"
        "当然，没有后台数据，我们不能说它一定卖得好，但从创意结构看，它确实更容易被理解和记住。"
        "你最近还看到哪些值得拆的广告？评论区发给我。"
    )
    return {
        "douyin_article": {
            "title": f"{brand}这条广告，真正高明的不是卖{product}",
            "hook": takeaway,
            "body": body,
            "cta": "你最近还看到哪些值得拆的广告？评论区发给我。",
            "hashtags": ["#广告拆解", "#营销观察", f"#{brand}", "#内容创作"],
        },
        "douyin_script": {
            "title": f"拆解{brand}这条广告",
            "duration_seconds": 75,
            "hook": f"{brand}这条广告，卖的可能根本不只是{product}。",
            "beats": [
                {"label": "结论", "script": takeaway},
                {"label": "结构", "script": "先把用户拉进场景，再给产品作为解决办法。"},
                {"label": "启发", "script": "可复用的是信息顺序，而不是照搬一句文案。"},
            ],
            "cta": "你最近还看到哪些值得拆的广告？评论区发给我。",
            "full_script": script,
        },
        "xiaohongshu": {
            "titles": [
                f"拆了{brand}这条广告，我发现它根本不只是在卖{product}",
                f"广告人视角：{brand}这条内容为什么容易被记住",
                f"这条广告最值得偷学的，是它的信息顺序",
            ],
            "body": body,
            "hashtags": ["#广告拆解", "#品牌营销", "#内容运营", "#创意灵感"],
            "image_card_ideas": [
                f"首图：{brand}这条广告，真正卖的是什么？",
                "第二张：前3秒钩子拆解",
                "第三张：场景-证明-行动结构",
                "第四张：可以复用与不能照搬的部分",
            ],
        },
    }
