from __future__ import annotations

from datetime import datetime
from typing import Any


CLAIM_LABELS = {
    "observed": "事实",
    "inferred": "推断",
    "hypothesis": "假设",
}

CONFIDENCE_LABELS = {
    "high": "高",
    "medium": "中",
    "low": "低",
}

VERDICT_LABELS = {
    "pass": "可发布",
    "review": "建议人工复核",
    "reject": "不建议直接发布",
}


def build_report_markdown(
    record: dict[str, Any],
    analysis: dict[str, Any],
    publishing: dict[str, Any] | None = None,
) -> str:
    publishing = publishing or {}
    brand = _text(record.get("brand_name"), "未识别品牌")
    product = _text(record.get("product_name"), "未识别产品")
    platform = _text(record.get("source_platform") or record.get("platform"), "未知平台")
    industry = _text(record.get("industry"), "未分类")
    created_at = _text(record.get("created_at"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    material = analysis.get("material_understanding") or {}
    audit = analysis.get("quality_audit") or {}
    meta = analysis.get("analysis_meta") or {}
    note = analysis.get("final_note") or {}
    scoring = analysis.get("scoring") or {}
    score_data = scoring.get("scoring", scoring) if isinstance(scoring, dict) else {}
    creative_dna = scoring.get("creative_dna", {}) if isinstance(scoring, dict) else {}
    evidence = material.get("evidence_ledger", []) if isinstance(material, dict) else []

    trust_score = _number(audit.get("trust_score", meta.get("trust_score", 0)))
    verdict = _text(audit.get("verdict") or meta.get("audit_verdict"), "review").lower()
    source_mode = _text(meta.get("source_mode"), "unknown")
    video_model = _text(meta.get("video_model"), "未记录")
    takeaway = _text(
        note.get("one_sentence_takeaway"),
        f"{brand}通过具体场景与信息顺序，让{product}更容易被理解和记住。",
    )

    lines = [
        f"# {brand}「{product}」广告创意研究报告",
        "",
        f"> **核心结论**  \n> {takeaway}",
        "",
        "| 报告信息 | 内容 |",
        "|---|---|",
        f"| 分析编号 | `{_cell(record.get('id') or '未记录')}` |",
        f"| 平台 / 行业 | {_cell(platform)} / {_cell(industry)} |",
        f"| 生成时间 | {_cell(created_at)} |",
        f"| 视频理解模型 | `{_cell(video_model)}` |",
        f"| 素材读取模式 | `{_cell(source_mode)}` |",
        "",
        "---",
        "",
        "## 01｜执行摘要",
        "",
        f"这份报告把**素材事实**、**策略推断**与**受众假设**分开呈现。当前可信度评分：**{trust_score}/100**，审查结论：**{VERDICT_LABELS.get(verdict, '建议人工复核')}**。",
        "",
        _trust_callout(audit, evidence),
        "",
        "## 02｜证据账本",
        "",
        "以下内容来自完整视频、关键帧、口播转写或屏幕文字。后续判断使用证据编号回溯。",
        "",
        "| 编号 | 时间 | 模态 | 可核验观察 | 原文 / 屏幕文字 | 置信度 |",
        "|---|---|---|---|---|---|",
    ]

    if evidence:
        for item in evidence:
            lines.append(
                "| {id} | {timestamp} | {modality} | {observation} | {quote} | {confidence} |".format(
                    id=_cell(item.get("id")),
                    timestamp=_cell(item.get("timestamp")),
                    modality=_cell(item.get("modality")),
                    observation=_cell(item.get("observation")),
                    quote=_cell(item.get("quote") or "—"),
                    confidence=_cell(CONFIDENCE_LABELS.get(str(item.get("confidence")), item.get("confidence") or "低")),
                )
            )
    else:
        lines.append("| — | — | — | 暂无可定位的视频证据 | — | 低 |")

    lines.extend(
        [
            "",
            "## 03｜创意评分",
            "",
            f"### {_text(score_data.get('overall_score'), '—')} 分 · {_text(score_data.get('tier'), '未评级')}",
            "",
            _text(score_data.get("score_breakdown_note"), "评分仅用于比较创意结构，不代表真实投放转化效果。"),
            "",
        ]
    )
    rationales = score_data.get("category_rationales", []) if isinstance(score_data, dict) else []
    if isinstance(rationales, list) and rationales:
        lines.extend(
            [
                "| 维度 | 分数 | 评分依据 | 证据 |",
                "|---|---:|---|---|",
            ]
        )
        for item in rationales:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"| {_cell(item.get('category'))} | {_cell(item.get('score'))} | "
                f"{_cell(item.get('reason'))} | {_cell(', '.join(item.get('evidence_ids', [])) or '—')} |"
            )
        lines.append("")

    lines.extend(
        [
            "## 04｜素材解构",
            "",
            *_material_deconstruction(material, evidence),
            "",
            "## 05｜广告策略分析",
            "",
            *_strategy_analysis(analysis.get("ad_strategy") or {}),
            "",
            "## 06｜用户洞察",
            "",
            *_user_insight_analysis(analysis.get("user_insight") or {}),
            "",
            "## 07｜宏观背景",
            "",
            *_macro_context_analysis(analysis.get("macro_context") or {}),
            "",
            "## 08｜对我的启发",
            "",
            *_inspiration_section(analysis, publishing),
            "",
            "## 09｜可复用的创意蓝图",
            "",
            *_creative_blueprint(creative_dna),
            "",
            "## 10｜风险、未知与验证建议",
            "",
            *_risk_section(audit),
            "",
            "## 11｜抖音发布包",
            "",
            *_douyin_section(publishing.get("douyin_article") or {}, publishing.get("douyin_script") or {}),
            "",
            "## 12｜小红书适配稿",
            "",
            *_xiaohongshu_section(publishing.get("xiaohongshu") or {}),
            "",
            "## 13｜方法说明",
            "",
            f"- 完整视频优先由 `{video_model}` 分析；失败时按关键帧视觉、文本顺序降级。",
            "- 事实必须进入证据账本；策略和人群结论必须标注为推断或假设。",
            "- 独立审查 Agent 与本地确定性门禁共同拦截无证据结论。",
            "- 发布稿通过双候选与正反顺序成对评审选出，以降低单次生成和位置偏差。",
            "- 本报告评估创意表达，不替代真实投放数据、消费者研究或法律合规审查。",
            "",
            "---",
            "",
            f"*AI-AD Evidence Desk · Report `{_text(record.get('id'), 'unknown')}` · {created_at}*",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _trust_callout(audit: dict[str, Any], evidence: list[dict[str, Any]]) -> str:
    unsupported = audit.get("unsupported_claims", []) if isinstance(audit, dict) else []
    limitations = audit.get("limitations", []) if isinstance(audit, dict) else []
    parts = [
        f"> **审查摘要**：共记录 **{len(evidence)}** 条可定位证据。",
    ]
    if unsupported:
        parts.append(f"发现 **{len(unsupported)}** 条未充分支持的结论，已从可发布上下文中排除。")
    if limitations:
        limitation = _text(limitations[0]).rstrip("。")
        parts.append(f"主要限制：{limitation}。")
    if len(parts) == 1:
        parts.append("未发现被本地门禁判定为无证据的公开结论。")
    return " ".join(parts)


def _material_deconstruction(material: dict[str, Any], evidence: list[dict[str, Any]]) -> list[str]:
    product = material.get("product_summary", {}) if isinstance(material, dict) else {}
    scene = material.get("scene_breakdown", {}) if isinstance(material, dict) else {}
    copy = material.get("copy_analysis", {}) if isinstance(material, dict) else {}
    visual = material.get("visual_elements", {}) if isinstance(material, dict) else {}
    return [
        "### 商品信息",
        "",
        "| 字段 | 内容 |",
        "|---|---|",
        f"| 品牌 | {_cell(product.get('brand'))} |",
        f"| 产品 | {_cell(product.get('product'))} |",
        f"| 品类 | {_cell(product.get('category'))} |",
        f"| 价格带 | {_cell(product.get('price_segment'))} |",
        f"| 核心卖点 | {_cell(product.get('usp'))} |",
        "",
        "### 画面解构",
        "",
        f"- **场景**：{_text(scene.get('setting'), '未识别')}",
        f"- **人物**：{_join(scene.get('characters'))}",
        f"- **关键动作**：{_join(scene.get('actions'))}",
        f"- **调性**：{_text(scene.get('tone'), '未识别')}",
        f"- **转场/节奏**：{_text(scene.get('transitions'), '未识别')}",
        "",
        "### 文案解构",
        "",
        f"- **开头/标题**：{_text(copy.get('headline'), '未识别')}",
        f"- **关键声称**：{_join(copy.get('key_claims'))}",
        f"- **行动号召**：{_text(copy.get('cta'), '未识别')}",
        f"- **文案风格**：{_text(copy.get('copy_style'), '未识别')}",
        f"- **声音与字幕**：口播 {_yes_no(copy.get('has_voiceover'))}；音乐 {_yes_no(copy.get('has_music'))}；屏幕字 {_yes_no(copy.get('has_text_overlay'))}",
        "",
        "### 视觉元素",
        "",
        f"- **镜头类型**：{_text(visual.get('shot_type'), '未识别')}",
        f"- **主色调**：{_join(visual.get('dominant_colors'))}",
        f"- **屏幕文字**：{_join(visual.get('text_overlays'))}",
        f"- **视觉效果**：{_join(visual.get('visual_effects'))}",
        "",
        "### 广告结构",
        "",
        f"- **前 3 秒**：{_first_text(copy.get('headline'), _evidence_text(evidence, 0), '以产品或情绪钩子建立第一眼注意。')}",
        f"- **中段**：{_first_text(_join(copy.get('key_claims')), _join(scene.get('actions')), '承接产品信息、证明点或场景演示。')}",
        f"- **结尾**：{_first_text(copy.get('cta'), _evidence_text(evidence, -1), '用行动入口、优惠或品牌信息完成收束。')}",
    ]


def _strategy_analysis(strategy: dict[str, Any]) -> list[str]:
    audience = strategy.get("target_audience_clue", {}) if isinstance(strategy, dict) else {}
    objective = strategy.get("ad_objective", {}) if isinstance(strategy, dict) else {}
    creative = strategy.get("creative_strategy", {}) if isinstance(strategy, dict) else {}
    positioning = strategy.get("competitive_positioning", {}) if isinstance(strategy, dict) else {}
    return [
        "### 投放判断",
        "",
        "| 字段 | 判断 |",
        "|---|---|",
        f"| 主要目标 | {_cell(objective.get('primary_goal'))} |",
        f"| 次要目标 | {_cell(objective.get('secondary_goal'))} |",
        f"| 漏斗位置 | {_cell(objective.get('funnel_stage'))} |",
        "",
        "### 目标人群线索",
        "",
        f"- **人口学线索**：{_join(audience.get('demographic_hints'))}",
        f"- **兴趣线索**：{_join(audience.get('interest_hints'))}",
        f"- **平台行为线索**：{_join(audience.get('platform_behavior_hints'))}",
        "",
        "### 创意结构拆解",
        "",
        f"- **钩子类型**：{_text(creative.get('hook_type'), '未识别')}",
        f"- **信任建立**：{_text(creative.get('trust_building'), '未识别')}",
        f"- **转化收尾**：{_text(creative.get('closing_tactic'), '未识别')}",
        f"- **叙事结构**：{_text(creative.get('narrative_structure'), '未识别')}",
        "",
        "### 竞争定位",
        "",
        f"- **差异化**：{_text(positioning.get('differentiation'), '未识别')}",
        f"- **对标对象**：{_text(positioning.get('benchmark_against'), '未识别')}",
        f"- **时机判断**：{_text(positioning.get('market_timing_rationale'), '未识别')}",
        "",
        "### 策略 Claim 与证据",
        "",
        *_claim_section(strategy),
    ]


def _user_insight_analysis(user: dict[str, Any]) -> list[str]:
    profile = user.get("target_user_profile", {}) if isinstance(user, dict) else {}
    pains = user.get("pain_points", {}) if isinstance(user, dict) else {}
    desire = user.get("desire_mapping", {}) if isinstance(user, dict) else {}
    return [
        "### 目标用户画像",
        "",
        "| 维度 | 假设 |",
        "|---|---|",
        f"| 年龄段 | {_cell(profile.get('age_range'))} |",
        f"| 性别倾向 | {_cell(profile.get('gender_tendency'))} |",
        f"| 城市等级 | {_cell(profile.get('city_tier'))} |",
        f"| 可能职业 | {_cell(_join(profile.get('occupation_clues')))} |",
        f"| 生活方式 | {_cell(_join(profile.get('lifestyle_tags')))} |",
        f"| 消费水平 | {_cell(profile.get('consumption_level'))} |",
        "",
        "### 痛点三层",
        "",
        f"- **显性痛点**：{_join(pains.get('explicit_pain'))}",
        f"- **隐性痛点**：{_join(pains.get('implicit_pain'))}",
        f"- **情绪痛点**：{_join(pains.get('emotional_pain'))}",
        "",
        "### 欲望三层",
        "",
        f"- **表面想要**：{_text(desire.get('surface_desire'), '未识别')}",
        f"- **真正想要**：{_text(desire.get('deep_desire'), '未识别')}",
        f"- **想成为谁**：{_text(desire.get('identity_desire'), '未识别')}",
        "",
        "### 用户洞察假设与证据",
        "",
        *_claim_section(user),
    ]


def _macro_context_analysis(macro: dict[str, Any]) -> list[str]:
    trends = macro.get("consumption_trends", []) if isinstance(macro, dict) else []
    platform = macro.get("platform_dynamics", {}) if isinstance(macro, dict) else {}
    sentiment = macro.get("social_sentiment", {}) if isinstance(macro, dict) else {}
    lines = [
        "### 消费趋势",
        "",
        "| 趋势 | 与广告的关联 | 置信度 |",
        "|---|---|---|",
    ]
    if isinstance(trends, list) and trends:
        for item in trends:
            if isinstance(item, dict):
                lines.append(
                    f"| {_cell(item.get('trend_name'))} | {_cell(item.get('relevance'))} | {_cell(item.get('confidence'))} |"
                )
    else:
        lines.append("| — | 未提供可审计趋势判断 | — |")
    lines.extend(
        [
            "",
            "### 平台生态",
            "",
            f"- **平台**：{_text(platform.get('platform'), '未识别')}",
            f"- **热点相关性**：{_text(platform.get('current_hotspot_relevance'), '未识别')}",
            f"- **内容趋势匹配**：{_text(platform.get('content_trend_match'), '未识别')}",
            f"- **算法友好度**：{_text(platform.get('algorithm_friendliness'), '未识别')}",
            "",
            "### 社会情绪",
            "",
            f"- **主导情绪**：{_text(sentiment.get('dominant_emotion'), '未识别')}",
            f"- **文化背景**：{_text(sentiment.get('cultural_context'), '未识别')}",
            f"- **价值观诉求**：{_text(sentiment.get('value_appeal'), '未识别')}",
            "",
            "### 时机判断",
            "",
            _text(macro.get("timing_analysis"), "未识别。"),
            "",
            "### 宏观判断与证据",
            "",
            *_claim_section(macro),
        ]
    )
    return lines


def _inspiration_section(analysis: dict[str, Any], publishing: dict[str, Any]) -> list[str]:
    material = analysis.get("material_understanding") or {}
    strategy = analysis.get("ad_strategy") or {}
    scoring = analysis.get("scoring") or {}
    score_container = scoring.get("scoring", scoring) if isinstance(scoring, dict) else {}
    dna = scoring.get("creative_dna", {}) if isinstance(scoring, dict) else {}
    creative = strategy.get("creative_strategy", {}) if isinstance(strategy, dict) else {}
    product = material.get("product_summary", {}) if isinstance(material, dict) else {}
    article = publishing.get("douyin_article") or {}
    xhs = publishing.get("xiaohongshu") or {}
    xhs_cards = xhs.get("image_card_ideas", []) if isinstance(xhs, dict) else []
    return [
        "### 如果我做抖音/自媒体",
        "",
        f"- 把开头做成一个可复述的反常识判断：{_text(article.get('title'), _text(creative.get('hook_type'), '先给观点，再给证据'))}。",
        "- 用证据编号组织口播，不把推断说成事实；优先讲最能被画面验证的 3 个点。",
        f"- 结构可以复用为：{_text(dna.get('narrative_template'), _text(creative.get('narrative_structure'), '钩子-证明-行动'))}。",
        f"- 评分启发：当前整体分 {_text(score_container.get('overall_score'), '—')}，优先补强最低置信度或最低分的环节，而不是只改标题。",
        "",
        "### 如果我做小红书",
        "",
        f"- 首图不要只写结论，改成“我看到了什么证据”：{_text(xhs_cards[0] if xhs_cards else '', '首图展示核心证据和反常识观点')}。",
        "- 正文采用“观察 -> 我的判断 -> 反向解释”的三段式，避免像硬广复述。",
        "- 卡片顺序建议：证据截图、结构拆解、用户心理、可复用模板、风险提醒。",
        "",
        "### 如果我做电商/品牌投放",
        "",
        f"- 把商品卖点拆成可验证信息：{_text(product.get('usp'), '先讲用户能直接看到或听到的卖点')}。",
        "- 价格、销量、功效类表达要留证据入口；没有外部来源时只写“素材标注/口播宣称”。",
        f"- 收口动作保持单一：{_text(creative.get('closing_tactic'), '给用户一个清晰搜索或下单入口')}。",
        "",
        "### 如果我做 AI 漫剧 / IP 内容",
        "",
        f"- 把广告的情绪公式迁移成剧情公式：{_text(dna.get('emotion_formula'), '先制造不确定，再给确定性出口')}。",
        "- 用角色困境替代商品参数：角色先遇到选择成本，再由一个可视化证据完成反转。",
        "- 每集结尾保留一个低门槛行动：关注下一集、评论选择、领取清单，而不是同时塞多个目标。",
        "",
        "### 下一轮可测试选题",
        "",
        "- A/B 测试 1：证据流拆解 vs 反常识拆解，比较完播和收藏。",
        "- A/B 测试 2：先讲价格锚点 vs 先讲用户疑虑，比较评论质量。",
        "- A/B 测试 3：单条广告深拆 vs 同品类三条横评，比较转发和私信咨询。",
    ]


def _claim_section(section: dict[str, Any]) -> list[str]:
    claims = section.get("claims", []) if isinstance(section, dict) else []
    if not isinstance(claims, list) or not claims:
        return ["暂无通过结构化证据门禁的结论。"]
    lines: list[str] = []
    for item in claims:
        if not isinstance(item, dict):
            continue
        if item.get("audit_status") == "rejected":
            continue
        label = CLAIM_LABELS.get(str(item.get("claim_type")), "推断")
        confidence = CONFIDENCE_LABELS.get(str(item.get("confidence")), "低")
        evidence = ", ".join(item.get("evidence_ids", [])) or "无直接证据"
        lines.append(f"### [{label} · 置信度{confidence}] {_text(item.get('claim'))}")
        lines.append("")
        lines.append(f"- **证据引用**：{evidence}")
        if item.get("counterpoint"):
            lines.append(f"- **反向解释**：{_text(item.get('counterpoint'))}")
        lines.append(f"- **支持状态**：`{_text(item.get('support_status'), 'unsupported')}`")
        lines.append("")
    return lines or ["暂无通过结构化证据门禁的结论。"]


def _creative_blueprint(value: dict[str, Any]) -> list[str]:
    if not isinstance(value, dict) or not value:
        return ["当前素材尚未形成稳定的可复用创意 DNA。"]
    return [
        f"- **叙事模板**：{_text(value.get('narrative_template'), '未提炼')}",
        f"- **情绪公式**：{_text(value.get('emotion_formula'), '未提炼')}",
        f"- **钩子结构**：{_text(value.get('hook_structure'), '未提炼')}",
        f"- **目标原型**：{_text(value.get('target_archetype'), '未提炼')}",
        f"- **可复用元素**：{_join(value.get('reusable_elements'))}",
    ]


def _risk_section(audit: dict[str, Any]) -> list[str]:
    items = []
    for label, key in (
        ("未支持结论", "unsupported_claims"),
        ("内部矛盾", "contradictions"),
        ("分析限制", "limitations"),
    ):
        values = audit.get(key, []) if isinstance(audit, dict) else []
        if isinstance(values, list):
            items.extend(f"- **{label}**：{_text(value)}" for value in values if _text(value))
    guidance = _text(audit.get("publication_guidance")) if isinstance(audit, dict) else ""
    if guidance:
        items.append(f"- **发布建议**：{guidance}")
    return items or ["- 未记录额外风险；仍建议发布前进行品牌、功效与平台规则复核。"]


def _douyin_section(article: dict[str, Any], script: dict[str, Any]) -> list[str]:
    if not article and not script:
        return ["暂无抖音发布稿。"]
    return [
        f"### 图文标题\n\n{_text(article.get('title'), '未生成')}",
        f"### 图文正文\n\n{_paragraphs(article.get('hook'), article.get('body'), article.get('cta'))}",
        f"**话题**：{_join(article.get('hashtags'), ' ')}",
        f"### {_text(script.get('duration_seconds'), 75)} 秒口播稿\n\n{_text(script.get('full_script'), '未生成')}",
    ]


def _xiaohongshu_section(value: dict[str, Any]) -> list[str]:
    if not value:
        return ["暂无小红书适配稿。"]
    titles = value.get("titles", [])
    title_lines = "\n".join(f"{index + 1}. {_text(title)}" for index, title in enumerate(titles)) if isinstance(titles, list) else ""
    cards = value.get("image_card_ideas", [])
    card_lines = "\n".join(f"- {_text(item)}" for item in cards) if isinstance(cards, list) else ""
    return [
        f"### 标题备选\n\n{title_lines or '未生成'}",
        f"### 正文\n\n{_text(value.get('body'), '未生成')}",
        f"**话题**：{_join(value.get('hashtags'), ' ')}",
        f"### 图片卡片建议\n\n{card_lines or '未生成'}",
    ]


def _paragraphs(*values: Any) -> str:
    return "\n\n".join(_text(value) for value in values if _text(value))


def _first_text(*values: Any) -> str:
    for value in values:
        text = _text(value)
        if text and text != "未识别":
            return text
    return "未识别"


def _evidence_text(evidence: list[dict[str, Any]], index: int) -> str:
    if not evidence:
        return ""
    try:
        item = evidence[index]
    except IndexError:
        return ""
    quote = _text(item.get("quote"))
    observation = _text(item.get("observation"))
    return quote or observation


def _yes_no(value: Any) -> str:
    if isinstance(value, bool):
        return "有" if value else "无"
    return _text(value, "未知")


def _join(value: Any, separator: str = "、") -> str:
    if isinstance(value, list):
        return separator.join(_text(item) for item in value if _text(item)) or "未识别"
    return _text(value, "未识别")


def _text(value: Any, default: Any = "") -> str:
    if value is None:
        return str(default)
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (str, int, float)):
        text = str(value).strip()
        return text or str(default)
    return str(default)


def _cell(value: Any) -> str:
    return _text(value, "—").replace("|", "\\|").replace("\n", "<br>")


def _number(value: Any) -> int:
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError):
        return 0
