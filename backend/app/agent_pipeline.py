"""Real LLM agent pipeline — 6 agents chained for ad analysis."""

from __future__ import annotations

import json
import logging
from typing import Any

from .analysis_quality import (
    apply_quality_gate,
    collect_claims,
    normalize_audit,
    normalize_evidence_ledger,
    publication_claims,
)
from .llm_client import (
    chat_completion,
    chat_completion_vision,
    chat_completion_video,
    is_configured,
    VIDEO_MODEL as DOUBAO_MODEL,
)

logger = logging.getLogger(__name__)

JSON_FORMAT = {"type": "json_object"}


# ═══════════════════════════════════════════════════════════
# Agent 1: Material Understanding
# ═══════════════════════════════════════════════════════════

AGENT1_VIDEO_SYSTEM = """你是一位严谨的广告视频证据分析师。你正在观看完整广告视频。首要任务不是给观点，而是建立可复核的证据账本。

输出以下 JSON（所有字段必须存在）：

{
  "evidence_ledger": [
    {
      "id": "E001",
      "timestamp": "00:00-00:03",
      "modality": "visual/audio/text",
      "observation": "只描述视频中明确出现或说出的内容",
      "quote": "口播或屏幕文字原句，没有则留空",
      "confidence": "high/medium/low"
    }
  ],
  "product_summary": {
    "brand": "品牌名（从视频中的logo、包装、口播中识别）",
    "product": "产品名",
    "category": "品类",
    "price_segment": "价格段位（从视频中的价格展示、优惠信息判断）",
    "usp": "核心卖点（一句话提炼）"
  },
  "scene_breakdown": {
    "setting": "场景描述（拍摄环境、背景）",
    "characters": ["出现的人物及其特征"],
    "actions": ["人物的关键动作序列"],
    "tone": "视频调性（焦虑/轻松/权威/感人/紧迫/搞笑/种草）",
    "transitions": "镜头切换和转场方式"
  },
  "copy_analysis": {
    "headline": "视频开头的第一句话或标题",
    "key_claims": ["视频中提到的所有关键声称"],
    "cta": "行动号召（引导用户做什么）",
    "copy_style": "口播/文案风格",
    "has_music": true,
    "has_voiceover": true,
    "has_text_overlay": true
  },
  "visual_elements": {
    "dominant_colors": ["主色调"],
    "text_overlays": ["视频中出现的所有屏幕叠加文字"],
    "shot_type": "镜头类型（特写/中景/远景/自拍/混剪）",
    "visual_effects": ["特效或转场效果"]
  },
  "confidence": {
    "overall": "high/medium/low",
    "notes": "分析可信度说明（视频清晰度、信息完整度等）"
  }
}

分析要点：
1. 每条事实先进入 evidence_ledger，使用时间戳定位，最多保留20条最关键证据
2. observation 只能写可看到、可听到或可读到的内容，不写“效果很好”“用户喜欢”等推测
3. 无法确认品牌、价格、销量或功效时写“信息不足”，禁止补全
4. quote 尽量保留原始口播或屏幕文字，不得虚构
5. product_summary 等总结必须由 evidence_ledger 支撑
6. 用中文输出，保持专业、克制、可审计"""

AGENT1_SYSTEM = """你是一位严谨的广告素材证据分析师。你的任务是对广告视频/图文进行细致解构，并区分事实与推断。

请严格按以下 JSON 结构输出（所有字段必须存在）：

{
  "evidence_ledger": [
    {
      "id": "E001",
      "timestamp": "关键帧或时间未知",
      "modality": "visual/audio/text",
      "observation": "素材明确出现的信息",
      "quote": "原始文字，没有则留空",
      "confidence": "high/medium/low"
    }
  ],
  "product_summary": {
    "brand": "品牌名",
    "product": "产品名",
    "category": "品类（如：美妆/精华液）",
    "price_segment": "价格段位",
    "usp": "核心卖点（一句话提炼）"
  },
  "scene_breakdown": {
    "setting": "场景描述",
    "characters": ["人物描述"],
    "actions": ["关键动作"],
    "tone": "调性（如：焦虑/轻松/权威/感人/紧迫）"
  },
  "copy_analysis": {
    "headline": "开头/标题",
    "key_claims": ["关键声称列表"],
    "cta": "行动号召",
    "copy_style": "文案风格（如：种草风/专家腔/故事型/对话体）"
  },
  "visual_elements": {
    "dominant_colors": ["主色调"],
    "text_overlays": ["屏幕叠加文字"],
    "shot_type": "镜头类型"
  },
  "confidence": {
    "overall": "high/medium/low",
    "notes": "分析可信度说明"
  }
}

分析要点：
1. 仔细观察画面中的人物、场景、产品、文字叠加
2. 分析文案结构：钩子→信息→信任→转化
3. 判断广告调性和目标情绪
4. 如果某些信息无法从素材中获取，标注为"信息不足"并在 confidence 中说明
5. 每个明确事实必须先记录到 evidence_ledger；不确定信息不得补全
6. 用中文输出，保持简洁专业"""


# ═══════════════════════════════════════════════════════════
# Agent 2: Ad Strategy
# ═══════════════════════════════════════════════════════════

AGENT2_SYSTEM = """你是一位资深广告投放策略分析师。你需要基于素材分析结果，反向推演广告的投放策略。

请严格输出以下 JSON：

{
  "claims": [
    {
      "claim": "一条策略判断",
      "claim_type": "inferred",
      "evidence_ids": ["E001"],
      "confidence": "high/medium/low",
      "counterpoint": "可能的另一种解释"
    }
  ],
  "target_audience_clue": {
    "demographic_hints": ["人口学线索"],
    "interest_hints": ["兴趣线索"],
    "platform_behavior_hints": ["平台行为线索"]
  },
  "ad_objective": {
    "primary_goal": "主要目标（如：快速转化/品牌认知/种草蓄水）",
    "secondary_goal": "次要目标",
    "funnel_stage": "转化漏斗位置"
  },
  "hook_pattern": {
    "primary": "主要钩子模式",
    "secondary": "辅助钩子模式",
    "evidence_ids": ["E001"]
  },
  "creative_strategy": {
    "hook_type": "钩子类型（如：痛点直击型/效果承诺型/价格冲击型/好奇心缺口型）",
    "trust_building": "信任建立方式",
    "closing_tactic": "转化收尾策略",
    "narrative_structure": "叙事结构"
  },
  "competitive_positioning": {
    "differentiation": "差异化策略",
    "benchmark_against": "对标竞品类型",
    "market_timing_rationale": "投放时机判断"
  },
  "confidence": {
    "overall": "high/medium/low",
    "notes": "分析可信度说明"
  }
}

分析要点：
1. 从素材反推目标人群画像——这条广告投给了谁？
2. 判断广告的核心目标：直接转化 vs 心智占领 vs 种草蓄水
3. 拆解创意结构：前3秒怎么钩 → 中间怎么建立信任 → 结尾怎么转化
4. 分析竞争定位：差异化策略和对标竞品
5. claims 是最重要的输出。每条结论必须引用真实存在的 evidence_ids
6. 策略判断只能标记为 inferred 或 hypothesis，不得伪装成 observed
7. 无法由素材验证的投放效果、竞品和时机结论必须降低置信度
8. 用中文输出，保持专业但可读

钩子模式分类（hook_pattern.primary/secondary 必须从以下13种中选择，不得自行发明）：
  - POV代入：用第一人称视角直接建立代入感（"我用了X天后..."）
  - 信念挑战：质疑一个普遍认知（"你以为X，其实Y"）
  - 直接点名：用"如果你是X"句式直接标示目标受众
  - 规模声明：用一个超预期的数字/比例引起好奇（"卖出X万单"）
  - 信息缺口：前3秒不给答案，制造悬念让人必须看完
  - 结果前置：先展示使用后的效果/变化，再解释过程
  - 权威背书：专家/明星/KOL出现在前3秒建立信任
  - 情感引爆：用愤怒/恐惧/感动等强情绪立刻抓住注意力
  - 反常识：用一个违背直觉的事实或判断开篇
  - 场景还原：还原一个目标用户熟悉的日常场景引发共鸣
  - 价格锚定：用价格对比或超低价作为核心吸引点
  - 对比冲突：用使用前/后或A/B对比制造视觉冲击
  - 创始人叙事：用创始人/主理人的亲身经历建立信任"""


# ═══════════════════════════════════════════════════════════
# Agent 3: User Insight
# ═══════════════════════════════════════════════════════════

AGENT3_SYSTEM = """你是一位消费心理学专家，擅长分析广告背后的用户心理。

请严格输出以下 JSON：

{
  "claims": [
    {
      "claim": "一条用户洞察假设",
      "claim_type": "hypothesis",
      "evidence_ids": ["E001"],
      "confidence": "high/medium/low",
      "counterpoint": "该画像可能不成立的原因"
    }
  ],
  "target_user_profile": {
    "age_range": "年龄段",
    "gender_tendency": "性别倾向",
    "city_tier": "城市等级倾向",
    "occupation_clues": ["可能职业"],
    "lifestyle_tags": ["生活方式标签"],
    "consumption_level": "消费水平"
  },
  "pain_points": {
    "explicit_pain": ["显性痛点（用户自己知道的）"],
    "implicit_pain": ["隐性痛点（用户没意识到的）"],
    "emotional_pain": ["情绪痛点（深层情绪驱动）"]
  },
  "desire_mapping": {
    "surface_desire": "表面想要什么",
    "deep_desire": "真正想要什么",
    "identity_desire": "想成为什么样的人"
  },
  "confidence": {
    "overall": "low/medium/high",
    "notes": "分析可信度说明"
  }
}

分析要点：
1. 从价格、品类、平台推断目标用户的年龄/城市/消费力
2. 挖掘三层痛点：显性→隐性→情绪
3. 映射三层欲望：表面想要→真正想要→想成为谁
4. 思考：用户买单的不是产品功能，而是广告里那个"用了之后"的自己
5. 年龄、城市、职业、消费力通常是研究假设，不是素材事实
6. 每条 claims 必须引用证据；没有证据时明确低置信度
7. 用中文输出，心理洞察要有深度，但不得把品类刻板印象写成事实"""


# ═══════════════════════════════════════════════════════════
# Agent 4: Macro Context
# ═══════════════════════════════════════════════════════════

AGENT4_SYSTEM = """你是一位消费趋势与平台生态分析师。基于广告信息，分析宏观背景。

请严格输出以下 JSON：

{
  "claims": [
    {
      "claim": "一条平台或文化背景判断",
      "claim_type": "inferred",
      "evidence_ids": ["E001"],
      "confidence": "high/medium/low",
      "counterpoint": "时效性或数据限制"
    }
  ],
  "consumption_trends": [
    {
      "trend_name": "趋势名称",
      "relevance": "与该广告的关联",
      "confidence": "inferred/observed"
    }
  ],
  "platform_dynamics": {
    "platform": "平台名",
    "current_hotspot_relevance": "当前平台热点的相关性",
    "content_trend_match": "内容趋势匹配度",
    "algorithm_friendliness": "算法友好度判断"
  },
  "social_sentiment": {
    "dominant_emotion": "主导社会情绪",
    "cultural_context": "文化背景",
    "value_appeal": "价值观诉诸"
  },
  "timing_analysis": "时机分析（结合大促/季节/社会热点）",
  "confidence": {
    "overall": "low/medium/high",
    "notes": "分析可信度说明"
  }
}

分析要点：
1. 判断与当前消费趋势的关联（如成分党、平替经济、质价比等）
2. 分析平台生态：该平台对该品类的流量分配处于什么阶段
3. 社会情绪分析：广告借势了什么时代情绪
4. 时机判断：是否在大促/季节性节点投放
5. 未联网、未提供外部数据时，禁止声称“当前热点”“近期爆发”“平台正在扶持”
6. 只能描述长期内容规律，并明确时效性限制
7. 每条 claims 必须引用素材证据或标记低置信度
8. 用中文输出"""


# ═══════════════════════════════════════════════════════════
# Agent 5: Factuality Auditor
# ═══════════════════════════════════════════════════════════

AUDITOR_SYSTEM = """你是一位独立事实审查编辑。你的职责是质疑，而不是润色其他 Agent 的结论。

请输出严格 JSON：
{
  "trust_score": 0,
  "verdict": "pass/review/reject",
  "approved_claim_ids": ["C001"],
  "unsupported_claim_ids": ["C002"],
  "unsupported_claims": ["没有证据或证据不匹配的结论"],
  "contradictions": ["不同结论之间的矛盾"],
  "limitations": ["素材、转写、画面或外部数据限制"],
  "publication_guidance": "发布时应如何措辞和规避误导"
}

审查规则：
1. observed 必须被证据直接支持；inferred/hypothesis 必须明确使用判断性措辞
2. 不允许从一条广告推断真实销量、转化率、投放规模或消费者普遍态度
3. 不允许把未经联网验证的趋势称为“当前热点”
4. 推断不是错误：只要引用的证据能支撑其观察前提、claim_type 标注正确且没有冒充确定事实，应放入 approved_claim_ids
5. 无法验证推断的真实效果属于 limitations，不应仅因缺少转化数据就判定该推断 unsupported
6. 只有证据编号无效、引入不存在的事实、措辞越过 claim_type，才放入 unsupported_claim_ids
7. 每个输入 claim_id 必须且只能进入 approved_claim_ids 或 unsupported_claim_ids 之一
8. trust_score 衡量证据纪律，不衡量文案好不好看
9. 只输出 JSON"""


# ═══════════════════════════════════════════════════════════
# Agent 6: Note Writer
# ═══════════════════════════════════════════════════════════

AGENT5_SYSTEM = """你是一位顶级广告创意总监，撰写深刻的广告洞察笔记。

基于各 Agent 的分析结果，输出以下 JSON（markdown_content 先留空字符串，稍后单独生成）：

{
  "title": "[广告洞察] 品牌 - 产品",
  "one_sentence_takeaway": "一句话核心洞察（锋利、好记、能复述）",
  "tags": ["广告洞察", "行业", "品牌", "平台"],
  "fact_check_summary": {
    "observed_facts": ["素材中明确出现的事实，3-5条"],
    "user_provided_context": ["用户补充的信息"],
    "model_inference": ["模型推理的部分"],
    "uncertainty": ["不确定的部分"]
  }
}

要求：
1. 一句话带走要锋利、好记，让人看完能复述
2. fact_check_summary 要诚实区分事实和推理
3. 不得使用“让用户停留”“降低试错”“促成下单”“带来转化”等未经效果数据验证的因果表达
4. 对创意意图使用“试图”“意在”“我的判断是”，对视频原话使用“素材宣称”
5. 用中文输出"""


# ═══════════════════════════════════════════════════════════
# Agent 7: Scoring
# ═══════════════════════════════════════════════════════════

AGENT6_SYSTEM = (
    '你是一位广告创意量化评估专家。基于素材证据而不是想象进行评分。'
    '直接输出纯 JSON（不要 markdown 代码块包裹）。\n\n'
    '{"scoring":{"hook":{"hook_type":"类型","hook_type_score":3,"opening_impact":3,"curiosity_gap":3},'
    '"messaging":{"usp_clarity":3,"claim_credibility":3,"differentiation":3},'
    '"trust":{"endorsement_strength":3,"social_proof":3,"data_backing":3},'
    '"conversion":{"cta_clarity":3,"urgency":3,"low_barrier":3},'
    '"emotion":{"emotional_intensity":3,"emotional_precision":3,"resonance":3},'
    '"production":{"visual_quality":3,"audio_quality":3,"pacing":3},'
    '"innovation":{"creative_freshness":3,"category_breakthrough":3},'
    '"overall_score":60,"tier":"B级","tier_color":"#2d2d2d","score_breakdown_note":"简短说明",'
    '"category_rationales":[{"category":"钩子","score":3,"reason":"评分理由","evidence_ids":["E001"]}]},'
    '"creative_dna":{"narrative_template":"模板","emotion_formula":"公式","hook_structure":"钩子结构","target_archetype":"原型","reusable_elements":["元素"]},'
    '"swipe_tags":["#行业_x","#平台_x","#钩子_x"]}\n\n'
    '每个维度1-5分。加权:钩子20%+信息传递20%+转化20%+情绪15%+信任10%+制作10%+创新5%。'
    '评级:S(80+)/A(65-79)/B(50-64)/C(35-49)/D(0-34)。'
    '每个类别必须写评分锚点和证据编号；没有效果数据时只能评创意质量，不能推断转化表现。'
    'score_breakdown_note 100字内。中文。'
)


# ═══════════════════════════════════════════════════════════
# Pipeline
# ═══════════════════════════════════════════════════════════

def _ad_context(ad: dict) -> str:
    """Build text context from ad input."""
    parts = []
    if ad.get("ad_title"):
        parts.append(f"广告标题：{ad['ad_title']}")
    if ad.get("brand_name"):
        parts.append(f"品牌：{ad['brand_name']}")
    if ad.get("product_name"):
        parts.append(f"产品：{ad['product_name']}")
    if ad.get("industry"):
        parts.append(f"行业：{ad['industry']}")
    if ad.get("price_range"):
        parts.append(f"价格带：{ad['price_range']}")
    if ad.get("platform"):
        parts.append(f"平台：{ad['platform']}")
    if ad.get("seen_at"):
        parts.append(f"看到时间：{ad['seen_at']}")
    if ad.get("ad_copy"):
        parts.append(f"广告文案：\n{ad['ad_copy']}")
    if ad.get("scene_description"):
        parts.append(f"场景描述：\n{ad['scene_description']}")
    if ad.get("screenshot_description"):
        parts.append(f"截图描述：\n{ad['screenshot_description']}")
    if ad.get("user_context"):
        parts.append(f"用户补充信息：\n{ad['user_context']}")
    return "\n\n".join(parts)


def _compact_json(obj: dict) -> str:
    """Compact JSON without indentation to save tokens."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


# ═══════════════════════════════════════════════════════════
# Industry-specific analysis dimensions (inspired by claude-ads industry templates)
# ═══════════════════════════════════════════════════════════

_INDUSTRY_DIMENSIONS = {
    "美妆": (
        "美妆行业分析校准：\n"
        "  - 信任关键：KOL/成分党/素人实测，而非品牌知名度\n"
        "  - 常见钩子：素人试用对比、成分揭秘、大牌平替对标\n"
        "  - 转化驱动：使用场景共鸣（约会/通勤/聚会）、变美焦虑\n"
        "  - 竞争维度：成分对标（如'XX大牌同款成分'）、价格带定位\n"
        "  - 注意：美妆广告的'效果'多为光影+滤镜，需标注画面可信度"
    ),
    "食品": (
        "食品行业分析校准：\n"
        "  - 信任关键：产地实拍/工艺可视化/配料表特写\n"
        "  - 常见钩子：源头工厂直发、吃播体验、价格暴利揭秘\n"
        "  - 转化驱动：健康焦虑（0添加/无糖）、口感想象、家庭场景\n"
        "  - 竞争维度：配料对比、渠道差异（工厂vs超市）、新鲜度\n"
        "  - 注意：食品广告常夸大'源头''农家''手工'，需标注声称vs证据"
    ),
    "3C": (
        "3C/数码行业分析校准：\n"
        "  - 信任关键：参数实测/跑分/拆机实拍，而非广告词\n"
        "  - 常见钩子：价格屠夫、黑科技揭秘、参数碾压同价位\n"
        "  - 转化驱动：效率提升（省时间）、性价比（省预算）、场景痛点\n"
        "  - 竞争维度：同价位横向PK、跨价位越级挑战\n"
        "  - 注意：3C广告的'性能提升X%'需看是否有实测数据支撑"
    ),
    "教育": (
        "教育/知识付费行业分析校准：\n"
        "  - 信任关键：讲师履历/学员案例/课程大纲可验证性\n"
        "  - 常见钩子：反常识观点、薪资/Offer截图、免费课/资料引流\n"
        "  - 转化驱动：认知差制造（'原来这么简单'）、结果焦虑、沉没成本\n"
        "  - 竞争维度：传统教育vs新方式、自学vs系统学、国内vs海外\n"
        "  - 注意：教育广告的效果承诺需严格区分'学员案例'和'普遍预期'"
    ),
    "电商": (
        "电商/平台行业分析校准：\n"
        "  - 信任关键：销量数字/好评率/售后政策可验证\n"
        "  - 常见钩子：限时优惠倒计时、库存紧迫、性价比对比\n"
        "  - 转化驱动：价格刺激、社交证明（'XX万人已买'）、场景植入\n"
        "  - 竞争维度：平台比价、同款PK、渠道专属\n"
        "  - 注意：电商广告的价格优势常通过与模糊'市场价'对比制造，需标注"
    ),
    "金融": (
        "金融/保险行业分析校准：\n"
        "  - 信任关键：牌照资质/合规话术/大厂背书\n"
        "  - 常见钩子：利率对比、政策解读、真实用户案例\n"
        "  - 转化驱动：风险恐惧、收益预期、信任构建（大平台=安全）\n"
        "  - 竞争维度：传统银行vs互联网金融、渠道成本对比\n"
        "  - 注意：金融广告的收益承诺受监管约束，需标注'声称'vs'保证'"
    ),
    "游戏": (
        "游戏行业分析校准：\n"
        "  - 信任关键：实机画面/玩法演示/玩家评价\n"
        "  - 常见钩子：精彩操作集锦、剧情悬念、限时福利/首充\n"
        "  - 转化驱动：社交驱动（组队/公会）、成就系统、限时奖励\n"
        "  - 竞争维度：同类玩法对比、画质/流畅度、氪金度\n"
        "  - 注意：游戏广告常使用CG/开发中画面，需标注是否为实机录制"
    ),
}

_DEFAULT_INDUSTRY_GUIDE = (
    "通用分析校准：\n"
    "  - 从素材反推行业特征，不预设分析框架\n"
    "  - 重点关注：信任构建方式、转化路径、目标人群匹配度\n"
    "  - 注意区分行业通用做法 vs 本条广告的创新点"
)


def _industry_guide(industry: str) -> str:
    """Return industry-specific analysis guide for Agent 2 and Agent 3."""
    if not industry:
        return _DEFAULT_INDUSTRY_GUIDE
    for key, guide in _INDUSTRY_DIMENSIONS.items():
        if key in industry:
            return guide
    return _DEFAULT_INDUSTRY_GUIDE


def _ok(result: dict) -> bool:
    """Check if LLM result is valid (no error, no raw fallback)."""
    return "_error" not in result and "_raw" not in result


async def _agent1_text(ctx: str) -> dict:
    """Agent 1 text-only analysis."""
    return await chat_completion(
        system=AGENT1_SYSTEM,
        user=f"请分析以下广告素材（纯文字描述，不含图片）：\n\n{ctx}",
        response_format=JSON_FORMAT,
    )


async def run_agent_pipeline(
    ad: dict,
    frames_base64: list[dict] | None = None,
    video_path: str | None = None,
    video_url: str | None = None,
) -> dict:
    """Run the evidence-driven LLM pipeline.

    Args:
        ad: Ad input dict with fields like brand_name, product_name, etc.
        frames_base64: Optional list of {"base64": "...", "mime": "image/jpeg"} for vision analysis.
        video_path: Optional local video file path for doubao video understanding.
        video_url: Optional video URL for doubao video understanding.

    Returns:
        Complete analysis result dict matching the mock_pipeline output structure.
    """
    ctx = _ad_context(ad)

    # ── Agent 1: Material Understanding ──
    logger.info("Agent 1/7: Evidence extraction...")
    source_mode = "text"
    video_error = ""

    # Priority: doubao video > dmxapi vision > text-only
    if video_path or video_url:
        logger.info("Agent 1: Using Doubao video understanding via DMXAPI...")
        doubao_result = await chat_completion_video(
            model=DOUBAO_MODEL,
            system=AGENT1_VIDEO_SYSTEM,
            text=f"请分析这个广告视频。\n\n已知信息：\n{ctx}",
            video_path=video_path,
            video_url=video_url,
            max_tokens=4096,
            response_format=JSON_FORMAT,
        )
        if _ok(doubao_result):
            a1 = doubao_result
            source_mode = "video"
        else:
            video_error = str(doubao_result.get("_error") or "视频理解返回无效结果")
            if frames_base64:
                logger.warning(
                    "Doubao video failed: %s, falling back to frame vision",
                    video_error,
                )
                a1 = await chat_completion_vision(
                    system=AGENT1_SYSTEM,
                    text=f"请分析以下广告素材：\n\n{ctx}",
                    images=frames_base64,
                    response_format=JSON_FORMAT,
                )
                source_mode = "frames_fallback"
            else:
                logger.warning(
                    "Doubao video failed: %s, falling back to text",
                    video_error,
                )
                a1 = await _agent1_text(ctx)
                source_mode = "text_fallback"
    elif frames_base64:
        a1 = await chat_completion_vision(
            system=AGENT1_SYSTEM,
            text=f"请分析以下广告素材：\n\n{ctx}",
            images=frames_base64,
            response_format=JSON_FORMAT,
        )
        source_mode = "frames"
    else:
        a1 = await _agent1_text(ctx)

    evidence_ledger = normalize_evidence_ledger(a1)
    a1["evidence_ledger"] = evidence_ledger
    logger.info(
        "Agent 1 done: %s, evidence=%d",
        "OK" if _ok(a1) else f"ERROR: {a1.get('_error', 'JSON parse failed')}",
        len(evidence_ledger),
    )

    # ── Agent 2: Ad Strategy ──
    logger.info("Agent 2/7: Evidence-linked strategy...")
    industry_guide = _industry_guide(ad.get("industry", ""))
    a2 = await chat_completion(
        system=AGENT2_SYSTEM,
        user=f"行业分析指引：\n{industry_guide}\n\n素材分析：\n{_compact_json(a1)}\n\n广告原始信息：\n{ctx}",
        response_format=JSON_FORMAT,
    )
    a2 = apply_quality_gate(a2, evidence_ledger)
    logger.info("Agent 2 done: %s", "OK" if _ok(a2) else f"ERROR: {a2.get('_error', 'JSON parse failed')}")

    # ── Agent 3: User Insight ──
    logger.info("Agent 3/7: Audience hypotheses...")
    a3 = await chat_completion(
        system=AGENT3_SYSTEM,
        user=f"行业分析指引：\n{industry_guide}\n\n素材分析：\n{_compact_json(a1)}\n\n策略分析：\n{_compact_json(a2)}\n\n广告信息：\n{ctx}",
        response_format=JSON_FORMAT,
    )
    a3 = apply_quality_gate(a3, evidence_ledger)
    logger.info("Agent 3 done: %s", "OK" if _ok(a3) else f"ERROR: {a3.get('_error', 'JSON parse failed')}")

    # ── Agent 4: Macro Context ──
    logger.info("Agent 4/7: Context with time-sensitivity limits...")
    a4 = await chat_completion(
        system=AGENT4_SYSTEM,
        user=(
            f"证据账本：\n{_compact_json({'evidence_ledger': evidence_ledger})}"
            f"\n\n策略分析：\n{_compact_json(a2)}"
            f"\n\n用户洞察：\n{_compact_json(a3)}"
            f"\n\n广告信息：\n{ctx}"
        ),
        response_format=JSON_FORMAT,
    )
    a4 = apply_quality_gate(a4, evidence_ledger)
    logger.info("Agent 4 done: %s", "OK" if _ok(a4) else f"ERROR: {a4.get('_error', 'JSON parse failed')}")

    # ── Agent 5: Factuality audit ──
    all_claims = collect_claims(a2, a3, a4)
    for index, claim in enumerate(all_claims, start=1):
        claim["claim_id"] = f"C{index:03d}"
    logger.info("Agent 5/7: Independent factuality audit...")
    audit_raw = await chat_completion(
        system=AUDITOR_SYSTEM,
        user=(
            f"证据账本：\n{_compact_json({'evidence_ledger': evidence_ledger})}"
            f"\n\n待审查结论：\n{_compact_json({'claims': all_claims})}"
            f"\n\n广告原始信息：\n{ctx}"
        ),
        response_format=JSON_FORMAT,
    )
    audit = normalize_audit(audit_raw, claims=all_claims)
    unsupported_ids = set(audit["unsupported_claim_ids"])
    for claim in all_claims:
        claim["audit_status"] = (
            "rejected" if claim.get("claim_id") in unsupported_ids else "approved"
        )
    safe_claims = publication_claims(all_claims, audit)
    logger.info(
        "Agent 5 done: verdict=%s, trust=%s, unsupported=%d",
        audit["verdict"],
        audit["trust_score"],
        len(audit["unsupported_claims"]),
    )

    # ── Agent 6: Scoring ──
    logger.info("Agent 6/7: Anchored scoring...")
    a6 = await chat_completion(
        system=AGENT6_SYSTEM,
        user=(
            f"证据账本：\n{_compact_json({'evidence_ledger': evidence_ledger})}"
            f"\n\n通过门禁的结论：\n{_compact_json({'claims': safe_claims})}"
            f"\n\n事实审查：\n{_compact_json(audit)}"
            f"\n\n广告信息：\n{ctx}"
        ),
        max_tokens=4096,
        response_format=JSON_FORMAT,
    )
    logger.info("Agent 6 done: %s", "OK" if _ok(a6) else f"ERROR: {a6.get('_error', 'JSON parse failed')}")

    # ── Agent 7: Editorial metadata ──
    logger.info("Agent 7/7: Editorial metadata...")
    a5_user = f"""素材分析：
{_compact_json(a1)}

通过审查的结论：
{_compact_json({"claims": safe_claims})}

事实审查：
{_compact_json(audit)}

评分：
{_compact_json(a6)}

广告信息：
{ctx}"""

    a5a = await chat_completion(
        system=AGENT5_SYSTEM,
        user=a5_user,
        response_format=JSON_FORMAT,
    )
    logger.info("Agent 7 done: %s", "OK" if _ok(a5a) else f"ERROR: {a5a.get('_error', 'JSON parse failed')}")

    # Combine
    note = a5a if _ok(a5a) else {}
    note["markdown_content"] = ""
    if not _ok(a5a):
        logger.warning("Agent 7 failed, note metadata will be minimal")

    observed_facts = [item["observation"] for item in evidence_ledger]
    model_inference = [
        item["claim"] for item in safe_claims
        if item.get("claim_type") in {"inferred", "hypothesis"}
    ]
    fact_summary = note.get("fact_check_summary")
    if not isinstance(fact_summary, dict):
        fact_summary = {}
    fact_summary.update(
        {
            "observed_facts": observed_facts,
            "model_inference": model_inference,
            "uncertainty": audit["limitations"] + audit["unsupported_claims"],
        }
    )
    note["fact_check_summary"] = fact_summary

    return {
        "material_understanding": a1,
        "ad_strategy": a2,
        "user_insight": a3,
        "macro_context": a4,
        "quality_audit": audit,
        "scoring": a6,
        "final_note": note,
        "observed_facts": observed_facts,
        "user_provided_context": note.get("fact_check_summary", {}).get("user_provided_context", []),
        "model_inference": model_inference,
        "uncertainty": fact_summary["uncertainty"],
        "analysis_meta": {
            "video_model": DOUBAO_MODEL,
            "source_mode": source_mode,
            "video_error": video_error or None,
            "evidence_count": len(evidence_ledger),
            "audit_verdict": audit["verdict"],
            "trust_score": audit["trust_score"],
        },
    }
