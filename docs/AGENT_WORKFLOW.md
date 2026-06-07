# AGENT_WORKFLOW — Agent 工作流设计 v0.2

> 版本: v0.2.0  
> 更新: 2026-06-07

---

## v0.1 → v0.2 变化

| 变化点 | v0.1 | v0.2 |
|--------|------|------|
| Agent 1 输入 | 纯文本 | 视频帧 + 语音转录 + OCR |
| Agent 4 输入 | 仅前序 Agent | 加上 newsbox 实时资讯 |
| 评分体系 | 无 | 28 维度 1-5 分量化 |
| 输出增强 | 无 | 创意 DNA + Swipe File 标签 |
| 新增 Agent | — | Agent 6: 评分 Agent（后处理） |

---

## Agent 总览

### 当前已实现的证据驱动链路

1. **视频证据 Agent**：`doubao-seed-2-0-lite-260215` 读取完整视频，生成 `E001` 格式的时间戳证据账本。
2. **策略 Agent**：每条判断输出 Claim ID、证据 ID、类型、置信度和反向解释。
3. **受众 Agent**：默认把年龄、偏好和动机写成假设，不把品类刻板印象当事实。
4. **语境 Agent**：无实时来源时禁止宣称“当前热点”或平台正在扶持。
5. **事实审查 Agent**：把每个 Claim 放入批准或驳回列表；本地门禁再次校验非法证据引用。
6. **评分 Agent**：使用评分锚点和证据编号，只评价创意表达，不推断真实转化。
7. **编辑 Agent**：生成两套不同角度，按正序和倒序各评一次，降低位置偏差。

最终报告由确定性构建器生成，不再依赖模型自由控制 Markdown 章节。网页、Markdown 和 PDF 共用同一份结构化结果。

| # | Agent 名称 | 职责 | 建议模型 | 环境变量 |
|---|-----------|------|---------|---------|
| 1 | 素材理解 Agent | 解构视频内容（画面+语音+文字） | 多模态（视觉+文本） | `MATERIAL_AGENT_MODEL` |
| 2 | 广告策略 Agent | 投放策略 + 创意结构 | 推理能力强 | `STRATEGY_AGENT_MODEL` |
| 3 | 用户洞察 Agent | 画像 + 痛点三层 + 欲望三层 | 同理心理解 | `USER_INSIGHT_AGENT_MODEL` |
| 4 | 宏观背景 Agent | 趋势 + 平台 + 社会情绪（含实时资讯） | 知识面广 | `MACRO_AGENT_MODEL` |
| 5 | 笔记写作 Agent | 汇总 + Markdown | 写作能力强 | `NOTE_WRITER_AGENT_MODEL` |
| 6 | 评分 Agent（新增） | 28 维度评分 + 创意 DNA 提取 | 结构化输出 | `SCORING_AGENT_MODEL` |

---

## Agent 1: 素材理解 Agent（增强）

### 输入增强

v0.2 新增多模态输入：

```json
{
  "source": {
    "platform": "抖音",
    "url": "https://v.douyin.com/xxx/",
    "parse_status": "success"
  },
  "metadata": {
    "title": "string",
    "author": "string",
    "like_count": "int | null",
    "comment_count": "int | null",
    "share_count": "int | null",
    "duration_seconds": "int"
  },
  "transcript": {
    "full_text": "string (Whisper 转录全文)",
    "segments": [{"start": 0.0, "end": 2.5, "text": "..."}]
  },
  "frames": [
    {
      "timestamp": 0.0,
      "description": "视觉模型对帧的描述",
      "detected_text": "OCR 提取的文字",
      "scene_type": "特写/中景/远景",
      "dominant_colors": ["#xxx"],
      "faces": [{"gender": "...", "age_range": "...", "expression": "..."}]
    }
  ],
  "comments": [
    {"text": "...", "likes": 100}
  ],
  "user_context": "string | null",
  "seen_at": "string | null"
}
```

### 输出 JSON Schema

在 v0.1 基础上增加：

```json
{
  "transcript_analysis": {
    "hook_sentence": "前3秒说的第一句话",
    "key_phrases": ["重复出现的关键词"],
    "speaking_style": "口语化/专家腔/种草风/故事型",
    "speaking_speed": "快/中/慢",
    "emotional_curve": [{"time": "0-5s", "emotion": "好奇"}, {"time": "5-15s", "emotion": "焦虑"}, ...]
  },
  "frame_analysis": {
    "scene_changes": 8,
    "visual_style": "明亮暖色调/暗调高级感/素人实拍/棚拍精致",
    "product_appearances": 5,
    "text_overlay_count": 12,
    "shot_types_used": ["特写", "中景", "产品展示"],
    "color_palette": {"primary": "#xxx", "secondary": "#xxx"}
  },
  "comment_analysis": {
    "top_comments": ["..."],
    "sentiment_summary": "正面/中性/负面",
    "user_questions": ["用户问得最多的问题"]
  }
}
```

### System Prompt（增强）

在原 prompt 基础上追加：

```
你现在分析的广告素材来自视频链接。你拥有以下信息：
1. 视频的语音转录（口播文案）
2. 关键帧的画面描述
3. 画面中出现的文字（OCR）
4. 评论区高赞内容

## 新增任务
- 分析语音的情绪曲线：视频在不同时间段传递了什么情绪？
- 分析画面的视觉风格和节奏：几秒换一次画面？什么色调？
- 从评论区提取用户真实反馈：用户关心什么？问什么？

## 输出要求
- 严格按 JSON Schema 输出
- observed_facts 和 model_inference 必须分开标注
```

---

## Agent 2: 广告策略 Agent

v0.1 基础上的增强：增加「互动数据」参考。

新增输出字段：

```json
{
  "engagement_analysis": {
    "engagement_rate_estimate": "根据点赞/评论/分享推断的互动水平",
    "comment_feedback_alignment": "评论区反馈和广告主想要的效果是否一致",
    "virality_potential": "高/中/低"
  }
}
```

---

## Agent 3: 用户洞察 Agent

v0.1 保持不变，但输入中增加了评论区数据，可以交叉验证用户画像推断。

---

## Agent 4: 宏观背景 Agent（增强）

### 输入增强：实时资讯

Agent 4 现在接收额外的 `live_intel` 字段：

```json
{
  "live_intel": {
    "fetch_time": "2026-06-07T10:00:00",
    "sources": [
      {
        "source": "X/Twitter",
        "headline": "某品牌 CEO 宣布新的市场策略...",
        "url": "...",
        "published_at": "2026-06-07T08:30:00",
        "relevance_score": 0.85
      }
    ],
    "trending_topics": ["618大促", "成分党护肤", "消费降级"],
    "industry_news": ["某竞品刚获得新融资", "新法规影响美妆广告"]
  }
}
```

### System Prompt 增强

```
你现在除了模型知识外，还有以下实时资讯可以参考：

{live_intel}

## 使用原则
1. 实时资讯优先于模型知识（如果时间冲突，以实时资讯为准）
2. 实时资讯需要标注来源和时间
3. 如果实时资讯和你的知识矛盾，在 confidence.notes 中说明
4. 如果实时资讯不足，用模型知识补充
```

---

## Agent 5: 笔记写作 Agent

v0.1 基础上新增输出章节（见 PRD v0.2）：

- 「零、质量评分」卡片（由 Agent 6 提供数据）
- 「八、创意 DNA」
- 「九、Swipe File 标签」

---

## Agent 6: 评分 Agent（新增）

### 职责

对所有前序 Agent 输出进行量化评分，提取创意 DNA。

### 输入

`AdInput` + `Agent 1-4 全部输出` + `实时资讯`

### 28 维度评分体系

```json
{
  "scoring": {
    "hook": {
      "hook_type": "痛点直击型",
      "hook_type_score": 4,
      "opening_impact": 5,
      "curiosity_gap": 3
    },
    "messaging": {
      "usp_clarity": 4,
      "claim_credibility": 3,
      "differentiation": 3
    },
    "trust": {
      "endorsement_strength": 2,
      "social_proof": 3,
      "data_backing": 2
    },
    "conversion": {
      "cta_clarity": 4,
      "urgency": 3,
      "low_barrier": 4
    },
    "emotion": {
      "emotional_intensity": 4,
      "emotional_precision": 5,
      "resonance": 4
    },
    "production": {
      "visual_quality": 3,
      "audio_quality": 3,
      "pacing": 4
    },
    "innovation": {
      "creative_freshness": 2,
      "category_breakthrough": 2
    },
    "overall_score": 72,
    "score_breakdown_note": "钩子和转化是亮点，但信任建立和创新不足"
  },
  "creative_dna": {
    "narrative_template": "问题-认同-方案-证明-行动",
    "emotion_formula": "焦虑 → 希望 → 自我奖赏",
    "hook_structure": "前2秒痛点画面 → 第3秒产品出现",
    "target_archetype": "30+ 轻熟女性，关注抗老",
    "reusable_elements": [
      "痛点画面开场可平移至其他护肤品类",
      "成分拆解节奏（每15秒一个成分）可复用",
      "限时优惠的紧迫感话术"
    ]
  },
  "swipe_tags": [
    "#钩子_痛点直击",
    "#情绪_焦虑转希望", 
    "#叙事_问题解决",
    "#行业_美妆",
    "#风格_专家背书",
    "#平台_抖音",
    "#评分_70以上"
  ]
}
```

### System Prompt

```
你是一个专业的广告创意评分师。你的任务不是写分析文章，而是给广告打分量化和提取可复用的创意基因。

## 评分原则
1. 每个维度 1-5 分，要有依据
2. 5 分 = 行业顶级水准，1 分 = 明显缺陷
3. 不要给中间分偷懒——如果是 3 分，说明为什么不是 4 也不是 2
4. 综合分不是平均分，是加权计算：
   - 钩子 20%、信息 20%、转化 20%、情绪 15%、信任 10%、制作 10%、创新 5%

## 创意 DNA 提取原则
1. 要具体到可操作的层面——不是「用了痛点」，而是「用镜子前的焦虑表情建立痛点」
2. 情绪公式要能套用到其他广告
3. reusable_elements 要能直接回答「我怎么偷学」

## 输出要求
- 严格按 JSON Schema 输出
```

### 建议模型

- 结构化输出能力强
- 推荐：GPT-4o / Claude Sonnet

### 失败兜底

如果该 Agent 失败：
- 笔记中不显示评分卡片
- 创意 DNA 从 Agent 2（策略）和 Agent 3（用户）中做简单提取
- Swipe File 标签用基础标签（行业/平台/品牌）

---

## 新增环境变量

```bash
# Agent 6: 评分 Agent
SCORING_AGENT_MODEL=

# 多媒体处理
WHISPER_MODEL_SIZE=medium    # tiny/base/small/medium/large-v3
VISION_MODEL=                # 视觉分析模型（如果和文本模型不同）

# 实时资讯
NEWSBOX_UPDATE_INTERVAL=21600  # 6 小时
NEWSBOX_MAX_SOURCES=10
```

---

## Agent 间数据流（v0.2 完整版）

```
视频链接
    ↓
Layer 1: 内容抓取 → VideoFile + Metadata + Comments
    ↓
Layer 2: 多媒体理解 → Transcript + FrameAnalysis + OCR
    ↓
Layer 3: 实时资讯 → LiveIntel
    ↓
┌───────────────────────────────────────────┐
│ Agent 1 (素材理解) ← VideoFile + Transcript + Frames + OCR + Comments
│   → MaterialAnalysis
├───────────────────────────────────────────┤
│ Agent 2 (广告策略) ← AdInput + MaterialAnalysis + Comments
│   → StrategyAnalysis
├───────────────────────────────────────────┤
│ Agent 3 (用户洞察) ← AdInput + MaterialAnalysis + StrategyAnalysis + Comments
│   → UserInsight
├───────────────────────────────────────────┤
│ Agent 4 (宏观背景) ← AdInput + StrategyAnalysis + UserInsight + LiveIntel ★
│   → MacroAnalysis
├───────────────────────────────────────────┤
│ Agent 5 (笔记写作) ← 所有前序 Agent 输出 + AdInput
│   → FinalNote (.md)
├───────────────────────────────────────────┤
│ Agent 6 (评分) ← Agent 1-4 输出 + FinalNote
│   → Scoring + CreativeDNA + SwipeTags
└───────────────────────────────────────────┘
    ↓
Layer 5: 知识库 → embedding → FAISS → Swipe File
    ↓
Layer 6: 输出 → Markdown + ScoreCard + SwipeFile Tags
```

---

## 失败兜底总览（v0.2）

| 失败场景 | v0.1 策略 | v0.2 增强 |
|----------|----------|----------|
| 链接解析失败 | — | 回退手动表单 |
| 视频下载失败 | — | 跳过视频，只用元数据 |
| Whisper 转录失败 | — | 标记「无语音转录」 |
| Agent 4 无实时资讯 | 用模型知识 | newsbox 兜底：用模型知识（同 v0.1） |
| Agent 6 失败 | — | 不显示评分，基础 Swipe 标签 |
| FAISS 未就绪 | — | 跳过向量搜索 |
