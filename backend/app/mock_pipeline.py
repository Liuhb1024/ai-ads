"""
Mock Agent Pipeline — generates realistic ad analysis without real LLM calls.

In mock mode, this module produces structured analysis results that look
like real multi-agent output.  When DMXAPI integration is enabled, each
function body will be replaced with actual LLM calls.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any


def _build_material_understanding(ad: dict) -> dict:
    brand = ad.get("brand_name", "某品牌")
    product = ad.get("product_name", "某商品")
    industry = ad.get("industry", "")
    ad_copy = ad.get("ad_copy", "")
    scene = ad.get("scene_description", "")
    screenshot = ad.get("screenshot_description", "")

    return {
        "product_summary": {
            "brand": brand,
            "product": product,
            "category": _infer_category(industry, product, ad_copy),
            "price_segment": ad.get("price_range", "不清楚"),
            "usp": _infer_usp(ad_copy, screenshot),
        },
        "scene_breakdown": {
            "setting": _infer_setting(scene),
            "characters": _infer_characters(scene),
            "actions": _infer_actions(scene),
            "tone": _infer_tone(ad_copy, scene),
        },
        "copy_analysis": {
            "headline": _extract_headline(ad_copy, ad.get("ad_title", "")),
            "key_claims": _extract_key_claims(ad_copy),
            "cta": _extract_cta(ad_copy),
            "copy_style": _infer_copy_style(ad_copy),
        },
        "visual_elements": {
            "dominant_colors": _infer_colors(industry, screenshot),
            "text_overlays": _extract_text_overlays(screenshot),
            "shot_type": _infer_shot_type(screenshot, scene),
        },
        "confidence": {
            "overall": "medium",
            "notes": "素材信息来自用户文字描述，非原始视频。画面分析和颜色判断为模型推理。",
        },
    }


def _build_strategy(ad: dict, material: dict) -> dict:
    industry = ad.get("industry", "")
    price = ad.get("price_range", "")
    platform = ad.get("platform", "")
    product = material.get("product_summary", {})

    return {
        "target_audience_clue": {
            "demographic_hints": _infer_demographic(industry, price, product),
            "interest_hints": _infer_interests(industry, product),
            "platform_behavior_hints": _infer_platform_behavior(platform),
        },
        "hook_pattern": {
            "primary": _infer_hook_type(product),
            "secondary": "",
            "evidence_ids": ["E001"],
        },
        "ad_objective": {
            "primary_goal": _infer_primary_goal(industry, price),
            "secondary_goal": "品牌心智渗透",
            "funnel_stage": _infer_funnel_stage(industry),
        },
        "creative_strategy": {
            "hook_type": _infer_hook_type(product),
            "trust_building": _infer_trust_building(industry, product),
            "closing_tactic": _infer_closing(price),
            "narrative_structure": "问题-解决方案型",
        },
        "competitive_positioning": {
            "differentiation": f"在{industry}品类中，强调{'性价比' if price == '低价' else '品质感' if price == '中价' else '身份象征'}作为核心差异点",
            "benchmark_against": f"行业{industry}头部竞品",
            "market_timing_rationale": _infer_timing(platform, ad.get("seen_at", "")),
        },
        "confidence": {"overall": "medium", "notes": "缺乏真实投放数据，策略分析基于素材反推，置信度中等。"},
    }


def _build_user_insight(ad: dict, material: dict, strategy: dict) -> dict:
    industry = ad.get("industry", "")
    price = ad.get("price_range", "")
    product = material.get("product_summary", {})

    return {
        "target_user_profile": {
            "age_range": _infer_age(industry, price, product),
            "gender_tendency": _infer_gender(industry),
            "city_tier": _infer_city(price),
            "occupation_clues": _infer_occupation(industry),
            "lifestyle_tags": _infer_lifestyle(industry, platform=ad.get("platform", "")),
            "consumption_level": _infer_consumption(price),
        },
        "pain_points": {
            "explicit_pain": _explicit_pains(industry, product),
            "implicit_pain": _implicit_pains(industry),
            "emotional_pain": _emotional_pains(industry, product),
        },
        "desire_mapping": {
            "surface_desire": f"购买到好用的{product.get('product', '商品')}",
            "deep_desire": _deep_desire(industry, price),
            "identity_desire": _identity_desire(industry, price),
        },
        "confidence": {"overall": "low", "notes": "用户画像为基于行业常识的推理，不同地区的投放策略可能导致用户画像显著不同。"},
    }


def _build_macro_context(ad: dict, strategy: dict, insight: dict) -> dict:
    industry = ad.get("industry", "")
    platform = ad.get("platform", "抖音")
    price = ad.get("price_range", "")

    return {
        "consumption_trends": [
            {
                "trend_name": _trend_1(industry),
                "relevance": f"该广告直接呼应了{industry}行业的这一趋势",
                "confidence": "inferred",
            },
            {
                "trend_name": _trend_2(industry, price),
                "relevance": "广告的定价和沟通策略与此趋势一致",
                "confidence": "inferred",
            },
        ],
        "platform_dynamics": {
            "platform": platform,
            "current_hotspot_relevance": _platform_hotspot(platform, industry),
            "content_trend_match": _content_match(platform),
            "algorithm_friendliness": f"{platform}算法对{industry}类内容的流量分配处于{'红利期' if platform == '视频号' else '成熟期'}",
        },
        "social_sentiment": {
            "dominant_emotion": _dominant_emotion(industry, price),
            "cultural_context": _cultural_context(industry),
            "value_appeal": _value_appeal(industry, price),
        },
        "timing_analysis": _timing_analysis(industry, platform, ad.get("seen_at", "")),
        "confidence": {"overall": "low", "notes": "宏观趋势判断依赖模型的世界知识，未接入实时数据源。趋势名称和关联为推理结果。"},
    }


def _build_final_markdown(ad: dict, material: dict, strategy: dict, insight: dict, macro: dict, scoring: dict | None = None) -> dict:
    brand = ad.get("brand_name", "某品牌")
    product = ad.get("product_name") or "某商品"
    industry = ad.get("industry", "未知行业")
    platform = ad.get("platform", "未知平台")
    price = ad.get("price_range") or "未标注"
    seen = ad.get("seen_at") or "未记录"
    ad_title = ad.get("ad_title") or "无标题"

    ps = material.get("product_summary", {})
    scene = material.get("scene_breakdown", {})
    copy_a = material.get("copy_analysis", {})
    obj = strategy.get("ad_objective", {})
    creative = strategy.get("creative_strategy", {})
    compete = strategy.get("competitive_positioning", {})
    profile = insight.get("target_user_profile", {})
    pains = insight.get("pain_points", {})
    desires = insight.get("desire_mapping", {})
    trends = macro.get("consumption_trends", [])
    platform_d = macro.get("platform_dynamics", {})
    sentiment = macro.get("social_sentiment", {})

    # Build scoring markdown before the main body
    scoring_md = ""
    if scoring:
        sc = scoring.get("scoring", {})
        dna = scoring.get("creative_dna", {})
        swipe_tags = scoring.get("swipe_tags", [])
        overall = sc.get("overall_score", 0)
        scoring_md = f"""---
## 七、28 维度评分卡

**综合得分：{overall}/100** · {sc.get('tier', '')}

| 类别 (权重) | 维度 | 分数 |
|-------------|------|------|
| 钩子 (20%) | 钩子类型：{sc.get('hook', {}).get('hook_type', '-')} | {sc.get('hook', {}).get('hook_type_score', '-')} |
|  | 开场冲击力 | {sc.get('hook', {}).get('opening_impact', '-')} |
|  | 好奇心缺口 | {sc.get('hook', {}).get('curiosity_gap', '-')} |
| 信息传递 (20%) | USP 清晰度 | {sc.get('messaging', {}).get('usp_clarity', '-')} |
|  | 声称可信度 | {sc.get('messaging', {}).get('claim_credibility', '-')} |
|  | 差异化程度 | {sc.get('messaging', {}).get('differentiation', '-')} |
| 信任建立 (10%) | 背书强度 | {sc.get('trust', {}).get('endorsement_strength', '-')} |
|  | 社交证明 | {sc.get('trust', {}).get('social_proof', '-')} |
|  | 数据支撑 | {sc.get('trust', {}).get('data_backing', '-')} |
| 转化设计 (20%) | CTA 清晰度 | {sc.get('conversion', {}).get('cta_clarity', '-')} |
|  | 紧迫感 | {sc.get('conversion', {}).get('urgency', '-')} |
|  | 低门槛 | {sc.get('conversion', {}).get('low_barrier', '-')} |
| 情绪调动 (15%) | 情绪强度 | {sc.get('emotion', {}).get('emotional_intensity', '-')} |
|  | 情绪精准度 | {sc.get('emotion', {}).get('emotional_precision', '-')} |
|  | 共鸣程度 | {sc.get('emotion', {}).get('resonance', '-')} |
| 制作水准 (10%) | 画面质量 | {sc.get('production', {}).get('visual_quality', '-')} |
|  | 声音质量 | {sc.get('production', {}).get('audio_quality', '-')} |
|  | 节奏控制 | {sc.get('production', {}).get('pacing', '-')} |
| 创新性 (5%) | 创意新鲜度 | {sc.get('innovation', {}).get('creative_freshness', '-')} |
|  | 品类突破 | {sc.get('innovation', {}).get('category_breakthrough', '-')} |

{sc.get('score_breakdown_note', '')}

### 🧬 创意 DNA

- **叙事模板**：{dna.get('narrative_template', '-')}
- **情绪公式**：{dna.get('emotion_formula', '-')}
- **钩子结构**：{dna.get('hook_structure', '-')}
- **目标原型**：{dna.get('target_archetype', '-')}
- **可复用元素**：
{_bullet_list(dna.get('reusable_elements', []))}

### 🏷️ Swipe 标签

{' '.join(swipe_tags) if swipe_tags else '无标签'}

"""

    md = f"""# [广告洞察] {brand} - {product}

> 分析时间：{_now()}
> 平台来源：{platform}
> 行业：{industry}
> 可信度标注：✅ 事实  💬 用户提供  🧠 推理  ❓ 不确定

---

## 一、基本信息

| 字段 | 内容 |
|------|------|
| 品牌 | {brand} |
| 商品 | {product} |
| 行业 | {industry} |
| 价格带 | {price} |
| 平台 | {platform} |
| 看到时间 | {seen} |
| 广告标题 | {ad_title} |

---

## 二、素材解构（我看到了什么）

### 商品信息
- **品类**：{ps.get('category', '未知')}
- **核心卖点**：{ps.get('usp', '未明确')}
- **价格段位**：{ps.get('price_segment', '未知')}

### 画面
- **场景**：{scene.get('setting', '信息不足')}  ✅
- **人物**：{', '.join(scene.get('characters', [])) if scene.get('characters') else '未描述'}  ✅
- **关键动作**：{', '.join(scene.get('actions', [])) if scene.get('actions', []) else '未描述'}  ✅
- **调性**：{scene.get('tone', '未判断')}  🧠
- **镜头类型**：{material.get('visual_elements', {}).get('shot_type', '未判断')}  🧠

### 文案
- **开头/标题**：{copy_a.get('headline', '未提取')}  ✅
- **关键声称**：{_bullet_list(copy_a.get('key_claims', []))}
- **行动号召**：{copy_a.get('cta', '未明确')}  ✅
- **文案风格**：{copy_a.get('copy_style', '未判断')}  🧠

### 视觉元素
- **主色调**：{', '.join(material.get('visual_elements', {}).get('dominant_colors', []))}  🧠
- **屏幕文字**：{', '.join(material.get('visual_elements', {}).get('text_overlays', []))}  ✅

---

## 三、广告策略分析（为什么这么投）

### 投放判断
- **主要目标**：{obj.get('primary_goal', '未判断')}  🧠
- **次要目标**：{obj.get('secondary_goal', '未判断')}  🧠
- **转化漏斗位置**：{obj.get('funnel_stage', '未判断')}  🧠

我的判断：**这条广告的核心目的不是直接卖货，而是卡位。** 在{platform}上，{industry}品类的竞争已经不在产品层面，而在「谁先占领用户心智里的某个细分场景」。这条广告选择{creative.get('hook_type', '某个钩子')}作为钩子，是因为在这个场景下，用户的注意力窗口不到 3 秒，必须用最直接的利益点砸开。

### 创意结构拆解

**前 3 秒 — 怎么钩住用户**
钩子类型：**{creative.get('hook_type', '未分析')}**  🧠

这条广告没有用「你是否有XX问题」这种老套路，而是直接用{_hook_example(creative.get('hook_type', ''), brand)}。这让目标用户在刷到的第一瞬间就产生「这是在说我」的感觉。

**中段 — 怎么制造信任和欲望**
信任建立方式：**{creative.get('trust_building', '未分析')}**  🧠

有意思的地方：{_trust_insight(creative.get('trust_building', ''), brand)}。这种打法的聪明之处在于——它不直接说「我的产品好」，而是让用户自己得出这个结论。

**结尾 — 怎么转化**
转化方式：**{creative.get('closing_tactic', '未分析')}**  🧠

{_closing_insight(creative.get('closing_tactic', ''), price)}

### 竞争定位
- **差异化**：{compete.get('differentiation', '未分析')}  🧠
- **对标的可能是**：{compete.get('benchmark_against', '未判断')}  ❓
- **为什么这个时间投**：{compete.get('market_timing_rationale', '未分析')}  🧠

---

## 四、用户洞察（触达了谁）

### 目标用户画像
- **年龄**：{profile.get('age_range', '未推断')}  🧠
- **性别倾向**：{profile.get('gender_tendency', '未推断')}  🧠
- **城市等级**：{profile.get('city_tier', '未推断')}  🧠
- **可能职业**：{', '.join(profile.get('occupation_clues', []))}  🧠
- **生活方式**：{', '.join(profile.get('lifestyle_tags', []))}  🧠

### 痛点三层

**显性痛点**（用户自己知道的）
{_bullet_list(pains.get('explicit_pain', []))}

**隐性痛点**（用户没意识到的）
{_bullet_list(pains.get('implicit_pain', []))}

**情绪痛点**（背后驱动的情绪）
{_bullet_list(pains.get('emotional_pain', []))}

### 欲望三层
- **表面想要**：{desires.get('surface_desire', '未推断')}  🧠
- **真正想要**：{desires.get('deep_desire', '未推断')}  🧠
- **想成为谁**：{desires.get('identity_desire', '未推断')}  🧠

一个有意思的观察：这条广告在卖{product}，但真正在贩卖的是**{sentiment.get('dominant_emotion', '某种情绪价值')}**。用户买单的不是产品功能，是广告里那个「用了之后」的自己。

---

## 五、宏观背景（时代情绪与平台趋势）

### 消费趋势
{_trends_md(trends)}

### 平台生态
- {platform_d.get('current_hotspot_relevance', '未分析')}  🧠
- {platform_d.get('content_trend_match', '未分析')}  🧠
- {platform_d.get('algorithm_friendliness', '未分析')}  🧠

### 社会情绪
- **借势情绪**：{sentiment.get('dominant_emotion', '未分析')}  🧠
- **文化背景**：{sentiment.get('cultural_context', '未分析')}  🧠
- **价值观诉诸**：{sentiment.get('value_appeal', '未分析')}  🧠

### 时机判断
{macro.get('timing_analysis', '未分析')}  🧠

---

## 六、对我的启发

### 如果我在做自媒体
1. **偷学前 3 秒钩子**：{creative.get('hook_type', '这种')}钩子可以平移到我做{industry}相关内容的第一帧
2. **文案节奏**：{copy_a.get('copy_style', '这种')}风格适合在{platform}做口播，比念稿自然得多
3. **信任建立的节奏**：先抛出问题→认同你的焦虑→给出解法→展示效果，这个结构可以复用

### 如果我在做电商
1. **定价锚点**：{price}定价说明这个品类用户的决策成本{'低' if price == '低价' else '中' if price == '中价' else '高'}，详情页的信息密度可以参考
2. **痛点分层**：显性痛点做标题，隐性痛点做主图，情绪痛点做详情页故事——三层打透比堆功能参数有效

### 如果我在做 AI 漫剧 / IP 内容
1. **叙事结构可复用**：{creative.get('narrative_structure', '问题-解决方案')}结构天然适合短剧脚本
2. **情绪钩子**：把{creative.get('hook_type', '')}换成剧情冲突的形式，就是天然的前 3 秒钩子
3. **身份认同**：{desires.get('identity_desire', '用户想成为的那个人')}——这是角色的核心驱动力

{scoring_md}
## 八、分析可信度

### ✅ observed_facts（素材中明确出现的信息）
- 品牌：{brand}
- 商品：{product}
- 行业：{industry}
- 平台：{platform}
{chr(10).join(f'- {c}' for c in copy_a.get('key_claims', [])[:3])}

### 💬 user_provided_context（用户补充的信息）
- 价格判断：{price}
{chr(10).join(f'- {c}' for c in (ad.get('user_context', '') or '无').split('；')[:3]) if ad.get('user_context') else '- 用户未补充额外信息'}

### 🧠 model_inference（模型推理）
- 目标用户画像全部为推理
- 广告策略目标为推理
- 创意结构分析为推理
- 宏观趋势关联为推理
- 情绪痛点分析为推理

### ❓ uncertainty（不确定的部分）
- 品牌真实投放策略可能与分析不同
- 缺乏该广告的真实投放数据（CTR、转化率、投放时段）
- 宏观趋势判断基于模型的世界知识，未接入实时数据
- 目标用户画像为基于素材的逆向推断，非品牌方真实定向

---

## 标签

#广告洞察 #{industry} #{brand} #{platform} #素材分析

---

> 💡 **一句话带走**：{_one_liner(brand, product, creative.get('hook_type', ''), sentiment.get('dominant_emotion', ''))}

---

*本笔记由 ai-ad Mock 模式生成。当前未接入真实 LLM，分析内容为基于规则的推断。*
"""

    return {
        "title": f"[广告洞察] {brand} - {product}",
        "markdown_content": md,
        "tags": ["广告洞察", industry, brand, platform],
        "fact_check_summary": {
            "observed_facts": [
                f"品牌：{brand}",
                f"商品：{product}",
                f"行业：{industry}",
                f"平台：{platform}",
            ],
            "user_provided_context": [ad.get("user_context")] if ad.get("user_context") else ["用户未补充额外信息"],
            "model_inference": [
                "目标用户画像",
                "广告策略目标",
                "创意结构分析",
                "宏观趋势关联",
                "情绪痛点分析",
            ],
            "uncertainty": [
                "品牌真实投放策略可能不同",
                "缺乏真实投放数据",
                "宏观趋势为模型世界知识推断",
                "用户画像为逆向推断",
            ],
        },
        "one_sentence_takeaway": _one_liner(brand, product,
            creative.get('hook_type', ''), sentiment.get('dominant_emotion', '')),
    }


def _build_scoring(ad: dict, material: dict, strategy: dict, insight: dict) -> dict:
    """Agent 6: 28-dimension scoring + creative DNA extraction + swipe tags."""

    brand = ad.get("brand_name", "")
    product = ad.get("product_name", "")
    industry = ad.get("industry", "")
    platform = ad.get("platform", "")
    price = ad.get("price_range", "")
    ad_copy = ad.get("ad_copy", "")
    scene = ad.get("scene_description", "")
    screenshot = ad.get("screenshot_description", "")

    creative = strategy.get("creative_strategy", {})
    ps = material.get("product_summary", {})
    profile = insight.get("target_user_profile", {})

    # ── Score each dimension (1-5) with rule-based heuristics ──

    hook_type = creative.get("hook_type", "未知")
    has_copy = bool(ad_copy and len(ad_copy) > 20)
    has_scene = bool(scene and len(scene) > 20)
    has_screenshot = bool(screenshot and len(screenshot) > 20)
    detail_level = sum([has_copy, has_scene, has_screenshot])

    # Hook (20%)
    hook_type_score = 4 if "痛点" in hook_type else (3 if "效果" in hook_type or "价格" in hook_type else 3)
    opening_impact = min(5, 3 + detail_level)
    curiosity_gap = 3 if "好奇" in hook_type else (4 if "痛点" in hook_type else 2)

    # Messaging (20%)
    usp_clarity = min(5, 2 + (1 if ps.get("usp") and "未明确" not in str(ps.get("usp")) else 0) + (1 if has_copy else 0))
    claim_credibility = 3 if any(w in (ad_copy or "") for w in ["数据", "研究", "临床", "专利"]) else (2 if has_copy else 1)
    differentiation = 3 if price in ("中价", "高价") else (2 if price == "低价" else 2)

    # Trust (10%)
    trust_type = creative.get("trust_building", "")
    endorsement_strength = 3 if "对比" in trust_type or "数据" in trust_type else (2 if "共鸣" in trust_type else 1)
    social_proof = 3 if any(w in (ad_copy or "") for w in ["大家都在", "网红", "卖爆", "断货", "万人", "好评"]) else (2 if has_copy else 1)
    data_backing = 3 if "成分" in trust_type or "参数" in trust_type or "数据" in trust_type else (2 if has_copy else 1)

    # Conversion (20%)
    has_cta = any(w in (ad_copy or "") for w in ["点击", "下单", "购买", "链接", "橱窗", "私信", "关注", "领券", "限时", "抢", "优惠"])
    cta_clarity = 4 if has_cta else (2 if has_copy else 1)
    urgency = 3 if any(w in (ad_copy or "") for w in ["限时", "抢", "马上", "仅", "最后", "倒计时"]) else (2 if price == "低价" else 2)
    low_barrier = 4 if price in ("低价", "免费") else (3 if price == "中价" else 2)

    # Emotion (15%)
    emotional_intensity = 4 if "焦虑" in hook_type or "痛点" in hook_type else (3 if has_copy else 2)
    emotional_precision = min(5, 2 + detail_level)
    resonance = 4 if has_copy and len(ad_copy) > 50 else (3 if has_copy else 2)

    # Production (10%)
    visual_quality = min(5, 2 + has_scene + has_screenshot)
    audio_quality = 3 if has_copy else 1
    pacing = 3 if has_copy else 2

    # Innovation (5%)
    creative_freshness = 3 if "好奇" in hook_type else (2 if "痛点" in hook_type else 2)
    category_breakthrough = 2 if industry in ("教育", "游戏") else (3 if industry in ("美妆", "3C") else 2)

    # Weighted total (scale to 0-100)
    weights = {
        "hook": 0.20, "messaging": 0.20, "conversion": 0.20,
        "emotion": 0.15, "trust": 0.10, "production": 0.10, "innovation": 0.05,
    }

    dim_scores = {
        "hook": {"hook_type": hook_type, "hook_type_score": hook_type_score, "opening_impact": opening_impact, "curiosity_gap": curiosity_gap},
        "messaging": {"usp_clarity": usp_clarity, "claim_credibility": claim_credibility, "differentiation": differentiation},
        "trust": {"endorsement_strength": endorsement_strength, "social_proof": social_proof, "data_backing": data_backing},
        "conversion": {"cta_clarity": cta_clarity, "urgency": urgency, "low_barrier": low_barrier},
        "emotion": {"emotional_intensity": emotional_intensity, "emotional_precision": emotional_precision, "resonance": resonance},
        "production": {"visual_quality": visual_quality, "audio_quality": audio_quality, "pacing": pacing},
        "innovation": {"creative_freshness": creative_freshness, "category_breakthrough": category_breakthrough},
    }

    overall = 0
    for cat, dims in dim_scores.items():
        cat_avg = sum(v for k, v in dims.items() if k != "hook_type") / sum(1 for k in dims if k != "hook_type")
        overall += cat_avg * weights[cat] * 20  # scale 1-5 to 0-100

    overall_score = round(overall)

    # Score tier
    if overall_score >= 80:
        tier = "S级 · 行业标杆"
        tier_color = "#b8860b"
    elif overall_score >= 65:
        tier = "A级 · 表现优秀"
        tier_color = "#2d6a4f"
    elif overall_score >= 50:
        tier = "B级 · 中等偏上"
        tier_color = "#2d2d2d"
    elif overall_score >= 35:
        tier = "C级 · 有提升空间"
        tier_color = "#999999"
    else:
        tier = "D级 · 需要重做"
        tier_color = "#c1292e"

    # ── Creative DNA ──
    narrative_template = "问题-认同-方案-证明-行动" if "痛点" in hook_type else "好奇-揭示-满足-行动"
    emotion_formula = _infer_emotion_formula(hook_type)
    hook_structure = f"前2秒{creative.get('hook_structure_hint', _hook_hint(hook_type))}"
    target_archetype = f"{profile.get('age_range', '25-40')} {profile.get('gender_tendency', '通用')}，关注{industry}"

    reusable = []
    if has_copy:
        reusable.append(f"{brand}的{creative.get('hook_type', '钩子')}开场可平移至同类产品")
    if trust_type:
        reusable.append(f"信任建立方式（{trust_type}）可复用于{industry}品类")
    if has_cta:
        reusable.append("转化话术节奏可参考")
    if not reusable:
        reusable = ["信息不足，无法提取可复用元素"]

    # ── Swipe tags ──
    tags = _generate_swipe_tags(ad, hook_type, industry, platform, overall_score)

    return {
        "scoring": {
            **dim_scores,
            "overall_score": overall_score,
            "tier": tier,
            "tier_color": tier_color,
            "score_breakdown_note": _score_note(overall_score, dim_scores),
        },
        "creative_dna": {
            "narrative_template": narrative_template,
            "emotion_formula": emotion_formula,
            "hook_structure": hook_structure,
            "target_archetype": target_archetype,
            "reusable_elements": reusable,
        },
        "swipe_tags": tags,
    }


def _infer_emotion_formula(hook_type: str) -> str:
    if "痛点" in (hook_type or ""):
        return "焦虑 → 认同 → 希望 → 行动"
    if "效果" in (hook_type or ""):
        return "渴望 → 展示 → 惊喜 → 想要"
    if "价格" in (hook_type or ""):
        return "怀疑 → 惊讶 → 相信 → 抢购"
    return "好奇 → 满足 → 信任 → 行动"


def _hook_hint(hook_type: str) -> str:
    if "痛点" in (hook_type or ""):
        return "痛点画面 → 第3秒产品出现"
    if "效果" in (hook_type or ""):
        return "效果展示 → 产品揭秘"
    return "悬念/好奇 → 快速揭示"


def _score_note(overall: int, dims: dict) -> str:
    strengths = []
    weaknesses = []

    hook_avg = sum(v for k, v in dims["hook"].items() if k != "hook_type") / 3
    msg_avg = sum(dims["messaging"].values()) / 3
    conv_avg = sum(dims["conversion"].values()) / 3
    trust_avg = sum(dims["trust"].values()) / 3

    if hook_avg >= 3.5:
        strengths.append("钩子是亮点")
    if conv_avg >= 3.5:
        strengths.append("转化设计到位")
    if msg_avg >= 3.5:
        strengths.append("信息传递清晰")

    if trust_avg < 3:
        weaknesses.append("信任建立不足")
    if conv_avg < 2.5:
        weaknesses.append("转化路径模糊")
    if dims["innovation"]["creative_freshness"] < 3:
        weaknesses.append("创新性不够")

    parts = []
    if strengths:
        parts.append(" + ".join(strengths))
    if weaknesses:
        parts.append("但" + "、".join(weaknesses))
    return "，".join(parts) if parts else "表现均衡，无明显长短板"


def _generate_swipe_tags(ad: dict, hook_type: str, industry: str, platform: str, score: int) -> list:
    tags = [f"#行业_{industry}", f"#平台_{platform}"]

    if "痛点" in hook_type:
        tags.append("#钩子_痛点直击")
    elif "效果" in hook_type:
        tags.append("#钩子_效果承诺")
    elif "价格" in hook_type:
        tags.append("#钩子_价格冲击")
    elif "好奇" in hook_type:
        tags.append("#钩子_好奇心")

    price = ad.get("price_range", "")
    if price == "低价":
        tags.append("#价格_低价走量")
    elif price == "中价":
        tags.append("#价格_质价比")
    elif price == "高价":
        tags.append("#价格_高端定位")

    ad_copy = ad.get("ad_copy", "")
    if any(w in (ad_copy or "") for w in ["成分", "技术", "专利"]):
        tags.append("#信任_成分背书")
    elif any(w in (ad_copy or "") for w in ["数据", "研究", "%"]):
        tags.append("#信任_数据支撑")
    elif any(w in (ad_copy or "") for w in ["素人", "用户", "真实"]):
        tags.append("#信任_素人体验")

    if score >= 70:
        tags.append("#评分_70以上")
    elif score >= 50:
        tags.append("#评分_50-70")
    else:
        tags.append("#评分_50以下")

    tags.append(f"#品牌_{ad.get('brand_name', '未知')}")

    return tags[:8]


# ── Public API ─────────────────────────────────────────

def run_mock_pipeline(ad: dict) -> dict:
    """Run the full 6-agent mock pipeline and return the complete result."""

    material = _build_material_understanding(ad)
    strategy = _build_strategy(ad, material)
    insight = _build_user_insight(ad, material, strategy)
    macro = _build_macro_context(ad, strategy, insight)
    scoring = _build_scoring(ad, material, strategy, insight)
    note = _build_final_markdown(ad, material, strategy, insight, macro, scoring)

    return {
        "material_understanding": material,
        "ad_strategy": strategy,
        "user_insight": insight,
        "macro_context": macro,
        "scoring": scoring,
        "final_note": note,
        "observed_facts": note.get("fact_check_summary", {}).get("observed_facts", []),
        "user_provided_context": note.get("fact_check_summary", {}).get("user_provided_context", []),
        "model_inference": note.get("fact_check_summary", {}).get("model_inference", []),
        "uncertainty": note.get("fact_check_summary", {}).get("uncertainty", []),
    }


# ── Internal helpers (inference rules) ─────────────────

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _bullet_list(items: list) -> str:
    if not items:
        return "- 信息不足"
    return "\n".join(f"- {item}" for item in items)


def _infer_category(industry: str, product: str, ad_copy: str) -> str:
    if product and product != "某商品":
        return f"{industry}/{product}"
    return industry


def _infer_usp(ad_copy: str, screenshot: str) -> str:
    clues = []
    text = (ad_copy or "") + (screenshot or "")
    if any(w in text for w in ["28天", "7天", "14天", "一周", "一个月", "快"]):
        clues.append("见效快")
    if any(w in text for w in ["便宜", "只要", "仅需", "不到", "元"]):
        clues.append("价格低")
    if any(w in text for w in ["专利", "独家", "首创", "黑科技", "科研", "实验室"]):
        clues.append("技术/成分独特")
    if any(w in text for w in ["明星", "网红", "大家都在用", "卖爆", "断货"]):
        clues.append("社交证明")
    if any(w in text for w in ["安全", "温和", "无添加", "天然", "有机"]):
        clues.append("安全/天然")
    if any(w in text for w in ["年轻", "显", "龄", "纹", "老"]):
        clues.append("抗老/年轻化")
    return " + ".join(clues) if clues else "未明确提炼出核心卖点"


def _infer_setting(scene: str) -> str:
    if not scene:
        return "用户未描述场景"
    keywords = {
        "家": "居家环境", "房间": "居家环境", "客厅": "居家环境", "卧室": "居家环境", "浴室": "浴室",
        "办公室": "办公场景", "公司": "办公场景",
        "街头": "户外街头", "户外": "户外", "公园": "户外",
        "厨房": "厨房", "餐厅": "餐厅",
        "商场": "商场/零售", "店": "零售店面",
        "镜子": "室内（有镜子）",
        "车": "车内",
    }
    for k, v in keywords.items():
        if k in scene:
            return v
    return "室内场景（未详细描述）"


def _infer_characters(scene: str) -> list:
    if not scene:
        return []
    chars = []
    if any(w in scene for w in ["女性", "女生", "女孩", "妈妈", "她"]):
        chars.append("女性（约25-35岁）")
    if any(w in scene for w in ["男性", "男生", "男孩", "爸爸", "他"]):
        chars.append("男性")
    if any(w in scene for w in ["专家", "医生", "老师", "博士", "教授"]):
        chars.append("权威人物/专家")
    if any(w in scene for w in ["用户", "素人", "普通"]):
        chars.append("素人用户")
    if any(w in scene for w in ["网红", "博主", "达人", "KOL"]):
        chars.append("网红/KOL")
    return chars if chars else ["未提供人物信息"]


def _infer_actions(scene: str) -> list:
    if not scene:
        return []
    actions = []
    action_map = {
        "焦虑": "表现出焦虑/困扰",
        "自信": "展示自信状态",
        "出门": "出门/社交场景",
        "镜子": "照镜子/审视自己",
        "展示": "展示产品",
        "试用": "试用/使用产品",
        "对比": "前后对比展示",
        "笑": "微笑/开心",
        "惊讶": "惊喜/惊讶",
        "解释": "讲解/科普",
    }
    for k, v in action_map.items():
        if k in scene:
            actions.append(v)
    return actions if actions else ["未提供动作描述"]


def _infer_tone(ad_copy: str, scene: str) -> str:
    text = (ad_copy or "") + (scene or "")
    tone_map = {
        "焦虑": "焦虑", "担心": "焦虑", "怕": "焦虑",
        "笑": "轻松", "搞笑": "搞笑", "好玩": "轻松",
        "专业": "专业", "专家": "权威", "科研": "权威",
        "感人": "感人", "泪": "感人", "温暖": "温情",
        "紧迫": "紧迫", "限时": "紧迫", "马上": "紧迫",
        "夸张": "夸张", "震惊": "夸张",
        "日常": "日常", "生活": "日常",
    }
    for k, v in tone_map.items():
        if k in text:
            return v
    return "日常"


def _extract_headline(ad_copy: str, ad_title: str) -> str:
    if ad_copy:
        first_line = ad_copy.strip().split("\n")[0].strip()
        if len(first_line) <= 50:
            return first_line
        return first_line[:50] + "..."
    return ad_title or "未提取到标题"


def _extract_key_claims(ad_copy: str) -> list:
    if not ad_copy:
        return ["未提取到关键声称"]
    claims = []
    for sent in ad_copy.replace("！", "。").replace("？", "。").split("。"):
        sent = sent.strip()
        if sent and len(sent) > 5:
            claims.append(sent)
        if len(claims) >= 4:
            break
    return claims if claims else ["未提取到关键声称"]


def _extract_cta(ad_copy: str) -> str:
    if not ad_copy:
        return "未明确"
    cta_keywords = ["点击", "下单", "购买", "链接", "橱窗", "私信", "关注", "了解更多", "领券", "优惠", "限时", "抢"]
    for kw in cta_keywords:
        if kw in ad_copy:
            return f"引导用户{kw}"
    return "未明确发现 CTA"


def _infer_copy_style(ad_copy: str) -> str:
    if not ad_copy:
        return "未知"
    if any(w in ad_copy for w in ["姐妹们", "真的绝", "太好用", "种草", "冲"]):
        return "种草风（口语化+感叹）"
    if any(w in ad_copy for w in ["研究表明", "数据", "临床", "成分", "技术"]):
        return "专家腔（数据+成分背书）"
    if any(w in ad_copy for w in ["我", "以前", "后来", "现在", "那时候"]):
        return "故事型（第一人称经历）"
    if any(w in ad_copy for w in ["你", "你的", "你有没有", "是不是"]):
        return "对话体（直接与用户对话）"
    return "混合风格"


def _infer_colors(industry: str, screenshot: str) -> list:
    colors = []
    text = (screenshot or "").lower()
    if any(c in text for c in ["金", "黑", "深色"]):
        colors.append("黑金")
    if any(c in text for c in ["白", "浅色", "亮", "干净"]):
        colors.append("白色/浅色")
    if any(c in text for c in ["蓝", "科技"]):
        colors.append("蓝色系")
    if any(c in text for c in ["粉", "红", "暖"]):
        colors.append("暖色调")
    if any(c in text for c in ["绿", "天然", "植物"]):
        colors.append("绿色系")
    if not colors:
        if industry == "美妆":
            colors = ["浅粉/白色调（美妆常见）", "产品包装主色"]
        elif industry == "3C":
            colors = ["深色/金属（3C 常见）"]
        else:
            colors = ["未提供足够信息判断"]
    return colors


def _extract_text_overlays(screenshot: str) -> list:
    if not screenshot:
        return ["未提供截图描述"]
    # Look for quoted or explicitly mentioned text in the description
    overlays = []
    for part in screenshot.replace("'", '"').split('"'):
        part = part.strip()
        if part and len(part) > 3 and not part.startswith("标注"):
            overlays.append(part)
    return overlays[:3] if overlays else ["未提取到屏幕文字"]


def _infer_shot_type(screenshot: str, scene: str) -> str:
    text = (screenshot or "") + (scene or "")
    if any(w in text for w in ["特写", "近景", "细节", "局部"]):
        return "特写（产品/人脸细节）"
    if any(w in text for w in ["对比", "左右", "前后", "before", "after"]):
        return "对比展示"
    if any(w in text for w in ["中景", "半身"]):
        return "中景"
    if any(w in text for w in ["远景", "全景", "环境", "场景"]):
        return "远景/全景"
    if any(w in text for w in ["自拍", "前置", "对着镜头"]):
        return "自拍视角"
    return "未判断（信息不足）"


def _infer_demographic(industry: str, price: str, product: dict) -> list:
    hints = []
    if industry == "美妆":
        hints.append("女性为主，25-40岁")
        if "抗" in str(product) or "纹" in str(product):
            hints.append("关注抗老/护肤的轻熟龄群体")
    elif industry == "3C":
        hints.append("男性偏多，22-35岁")
        hints.append("关注科技/数码的理性消费者")
    elif industry == "教育":
        hints.append("有学习需求的人群，20-45岁")
    elif industry == "游戏":
        hints.append("男性为主，18-35岁")
    else:
        hints.append("泛消费人群，因品类覆盖较广")
    if price == "高价":
        hints.append("有一定消费能力")
    elif price == "低价":
        hints.append("价格敏感型消费者")
    return hints


def _infer_interests(industry: str, product: dict) -> list:
    interest_map = {
        "美妆": ["护肤/彩妆", "个人护理", "生活方式", "穿搭"],
        "食品": ["美食", "烹饪", "健康饮食", "零食"],
        "3C": ["科技数码", "新品发布", "评测", "性价比"],
        "教育": ["自我提升", "职业发展", "考证", "终身学习"],
        "电商": ["网购", "比价", "促销", "新品"],
        "金融": ["理财", "投资", "保险", "资产配置"],
        "游戏": ["手游/端游", "电竞", "二次元", "直播"],
    }
    return interest_map.get(industry, ["泛消费兴趣"])


def _infer_platform_behavior(platform: str) -> list:
    behavior_map = {
        "抖音": ["刷短视频消磨时间", "直播间下单", "被算法推荐种草"],
        "小红书": ["主动搜索种草", "看测评做购买决策", "图文+视频混合消费"],
        "视频号": ["朋友圈/群聊分享驱动", "中年用户增量", "信任链传播"],
        "快手": ["老铁文化", "信任主播", "高性价比消费"],
    }
    return behavior_map.get(platform, ["未知平台行为"])


def _infer_primary_goal(industry: str, price: str) -> str:
    if price == "低价":
        return "快速转化/走量"
    if price == "高价":
        return "品牌认知/心智占领"
    return "种草蓄水 + 引流转化"


def _infer_funnel_stage(industry: str) -> str:
    return "兴趣 → 考虑阶段（用户对品类有认知，需要建立品牌偏好）"


def _infer_hook_type(product: dict) -> str:
    usp = str(product.get("usp", ""))
    if "效" in usp or "快" in usp:
        return "效果承诺型钩子"
    if "便宜" in usp or "价" in usp:
        return "价格冲击型钩子"
    if "焦虑" in usp or "痛" in usp or "纹" in usp:
        return "痛点直击型钩子"
    return "好奇心缺口型钩子"


def _infer_trust_building(industry: str, product: dict) -> str:
    if industry == "美妆":
        return "成分拆解 + 效果对比"
    if industry == "3C":
        return "参数对比 + 实测数据"
    if industry == "食品":
        return "原料溯源 + 制作过程展示"
    return "场景共鸣 + 素人体验"


def _infer_closing(price: str) -> str:
    if price == "低价":
        return "限时优惠 + 低门槛试用"
    if price == "高价":
        return "身份认同 + 社交证明"
    return "优惠券 + 信任背书"


def _infer_timing(platform: str, seen_at: str) -> str:
    if seen_at:
        month = seen_at.split("-")[1] if "-" in seen_at else ""
        month_map = {
            "01": "年货节/春节前", "02": "春节/情人节", "03": "38大促",
            "06": "618大促", "09": "开学季/99大促",
            "11": "双11大促", "12": "双12/年终",
        }
        if month in month_map:
            return f"可能是{month_map[month]}期间的投放"
    return f"在{platform}上的投放时机可能与品牌自身营销节奏相关"


def _infer_age(industry: str, price: str, product: dict) -> str:
    if industry == "美妆":
        return "25-40岁"
    if industry == "游戏":
        return "18-30岁"
    if industry == "教育":
        return "22-45岁"
    return "25-45岁（通用消费品核心人群）"


def _infer_gender(industry: str) -> str:
    if industry == "美妆":
        return "女性为主（约80%）"
    if industry in ("3C", "游戏"):
        return "男性为主（约70%）"
    return "男女均有，无明显性别偏向"


def _infer_city(price: str) -> str:
    if price == "高价":
        return "一二线城市为主"
    if price == "低价":
        return "下沉市场（三四五线城市）占比高"
    return "一二三线城市均有分布"


def _infer_occupation(industry: str) -> list:
    occ_map = {
        "美妆": ["职场白领", "精致妈妈", "自由职业者"],
        "食品": ["家庭主妇/主夫", "上班族", "学生"],
        "3C": ["程序员/工程师", "学生", "数码爱好者"],
        "教育": ["职场人", "应届生", "转行者"],
    }
    return occ_map.get(industry, ["泛消费人群"])


def _infer_lifestyle(industry: str, platform: str = "") -> list:
    tags = []
    if industry == "美妆":
        tags = ["注重形象管理", "喜欢刷小红书/抖音", "愿意为颜值花钱", "关注抗老/保养"]
    elif industry == "3C":
        tags = ["科技爱好者", "理性消费", "喜欢看测评", "早期尝鲜者"]
    elif industry == "食品":
        tags = ["关注健康", "喜欢尝新", "日常刷美食内容"]
    if platform == "小红书":
        tags.append("习惯主动搜索种草")
    elif platform == "抖音":
        tags.append("算法推荐驱动消费")
    return tags


def _infer_consumption(price: str) -> str:
    if price == "高价":
        return "中高消费水平，注重品质"
    if price == "低价":
        return "价格敏感，但愿意为「小确幸」花钱"
    return "中等消费水平"


def _explicit_pains(industry: str, product: dict) -> list:
    product_str = str(product)
    if "纹" in product_str or "老" in product_str:
        return ["皮肤出现皱纹/松弛", "看起来比实际年龄老", "已有的护肤routine效果不明显"]
    if "胖" in product_str or "肥" in product_str:
        return ["体重管理困难", "尝试过多种减肥方法效果不佳"]
    return ["对现有解决方案不满意", "想解决某个具体问题但没找到好方法"]


def _implicit_pains(industry: str) -> list:
    pain_map = {
        "美妆": ["害怕衰老影响社交和职场竞争力", "觉得护肤routine太复杂但不敢简化"],
        "3C": ["现有设备体验有痛点但懒得换", "想提升效率但不知道怎么选"],
        "教育": ["焦虑职业发展但不知道学什么有用", "碎片化学习难以坚持"],
        "食品": ["想吃好的但怕不健康", "想控制饮食但管不住嘴"],
    }
    return pain_map.get(industry, ["信息过载，选择困难", "想消费但怕踩坑"])


def _emotional_pains(industry: str, product: dict) -> list:
    product_str = str(product)
    if "纹" in product_str or "老" in product_str:
        return ["对衰老的恐惧", "社交场合的自信心下降", "被同龄人比下去的焦虑"]
    if industry == "美妆":
        return ["对「不够好看」的深层焦虑", "想在社交中获得更多关注和认可"]
    return ["对现状的不满和无力感", "希望拥有更好的生活但不知从何下手"]


def _deep_desire(industry: str, price: str) -> str:
    if industry == "美妆":
        return "看起来年轻、状态好，在同龄人中保持竞争力"
    if industry == "3C":
        return "用科技提升效率，获得更多自由时间"
    return "用更少的精力获得更好的生活体验"


def _identity_desire(industry: str, price: str) -> str:
    if industry == "美妆":
        return "一个被岁月优待、看不出年龄的精致女性"
    if price == "高价":
        return "一个有品位、懂生活、有选择权的人"
    return "一个把生活过得井井有条、不被问题困扰的人"


def _trend_1(industry: str) -> str:
    trend_map = {
        "美妆": "成分党护肤 → 功效护肤 → 情绪护肤",
        "食品": "健康化零食 + 功能性食品崛起",
        "3C": "AI 硬件 + 消费电子性价比战争",
        "教育": "AI 时代的技能焦虑与终身学习",
    }
    return trend_map.get(industry, f"{industry}行业的消费升级趋势")


def _trend_2(industry: str, price: str) -> str:
    if price == "低价":
        return "消费降级下的「平替经济」"
    if price == "中价":
        return "中产消费的「质价比」转向"
    return f"品质消费：用户愿意为好体验支付溢价"


def _platform_hotspot(platform: str, industry: str) -> str:
    if platform == "抖音":
        return f"{industry}品类在抖音的内容电商转化率持续提升，品牌自播+达播双轮驱动"
    elif platform == "小红书":
        return f"{industry}是小红书的高频搜索品类，种草→购买的路径极短"
    elif platform == "视频号":
        return "视频号中老年增量用户+信任链传播机制，适合中高价品牌"
    return f"{platform}平台的{industry}内容生态正在成熟"


def _content_match(platform: str) -> str:
    if platform == "抖音":
        return "短视频+直播双引擎，内容必须在前3秒抓住注意力"
    if platform == "小红书":
        return "图文+视频混合，实用价值和审美价值并重"
    return "内容形式需要适配平台主流消费习惯"


def _dominant_emotion(industry: str, price: str) -> str:
    if industry == "美妆":
        return "「不想被岁月留下痕迹」的焦虑，和「用了它我就能保持状态」的希望"
    if price == "低价":
        return "「不贵但好用」的小确幸感"
    return "「我值得更好的」的自我奖赏心理"


def _cultural_context(industry: str) -> str:
    if industry == "美妆":
        return "颜值经济 + 年龄焦虑 + 社交媒体放大了「看起来年轻」的社会价值"
    return "社交媒体放大了「别人的生活看起来很完美」的比较心理"


def _value_appeal(industry: str, price: str) -> str:
    if industry == "美妆":
        return "爱自己 → 投资自己 → 年龄只是数字"
    if price == "低价":
        return "好东西不一定要贵"
    return "品质生活是每个人的权利"


def _timing_analysis(industry: str, platform: str, seen_at: str) -> str:
    parts = []
    if seen_at:
        parts.append(f"用户记录看到广告的时间为 {seen_at}")
    parts.append(f"在{platform}上，{industry}品牌正在争夺用户注意力窗口")
    parts.append("如果这是大促期间的投放，目的可能是借平台流量红利完成收割")
    return "；".join(parts)


def _trends_md(trends: list) -> str:
    if not trends:
        return "- 未分析"
    lines = []
    for i, t in enumerate(trends, 1):
        lines.append(f"{i}. **{t.get('trend_name', '')}**：{t.get('relevance', '')}（{t.get('confidence', '')}）")
    return "\n".join(lines)


def _hook_example(hook_type: str, brand: str) -> str:
    if "痛点" in (hook_type or ""):
        return f"一个具体的、让人不舒服的画面切入"
    if "效果" in (hook_type or ""):
        return f"一个「用了之后会怎样」的结果画面开场"
    if "价格" in (hook_type or ""):
        return f"一个让用户觉得「这么便宜？」的价格锚点开场"
    return "一个让人好奇的画面或问题开场"


def _trust_insight(trust_type: str, brand: str) -> str:
    if "成分" in (trust_type or "") or "参数" in (trust_type or ""):
        return "它没有堆一堆看不懂的成分表，而是只挑用户最关心的1-2个成分讲透"
    if "对比" in (trust_type or ""):
        return "对比不是简单的「我们更好」，而是让用户自己看到差异后自己下结论"
    if "共鸣" in (trust_type or ""):
        return "它用场景让用户觉得「对，我就是这样」，先认同用户再给方案"
    return "它通过具体场景建立信任，而不是空洞的品牌自夸"


def _closing_insight(closing: str, price: str) -> str:
    if "限时" in (closing or "") or "优惠" in (closing or ""):
        return f"价格已在前期锚定，结尾只需轻推一把——用限时/限量制造紧迫感。{price}定价的决策成本本就不高，一个明确的行动指令就够了。"
    return "结尾不给硬推销，而是让用户自己产生「我想要」的感觉——这是高级的转化方式。"


def _one_liner(brand: str, product: str, hook: str, emotion: str) -> str:
    if hook and emotion:
        return f"{brand}{product}这条广告的高明之处：用{hook}抓住注意力，用{emotion}完成转化，全程不靠降价。"
    return f"拆完这条{brand}广告最大的感受：好广告不是卖产品，是卖「用了之后的自己」。"
