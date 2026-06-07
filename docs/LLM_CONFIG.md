# LLM_CONFIG — 模型配置与 DMXAPI 接入 v0.2

> 版本: v0.2.0  
> 更新: 2026-06-07

---

## v0.1 → v0.2 变化

| 变化 | 说明 |
|------|------|
| 新增视觉模型配置 | 多模态分析需要 |
| 新增评分 Agent 模型 | Agent 6 独立配置 |
| 新增 Embedding 模型配置 | 向量化需要 |
| 新增本地模型配置 | Whisper, OCR 参数 |
| 新增资讯管道配置 | newsbox 相关 |

---

## 环境变量设计

### 当前实际使用的模型变量

```bash
DEFAULT_LLM_MODEL=claude-haiku-4-5-20251001
VISION_MODEL=gpt-5.4-nano
DOUBAO_VIDEO_MODEL=doubao-seed-2-0-lite-260215
```

素材优先级：

```text
本地完整视频 -> DOUBAO_VIDEO_MODEL
豆包失败 -> VISION_MODEL 分析关键帧
关键帧不可用 -> DEFAULT_LLM_MODEL 分析文本
```

每次结果都会在 `analysis_meta` 中记录 `video_model`、`source_mode`、`video_error`、`evidence_count` 和可信度审查状态。

### .env.example（v0.2 完整版）

```bash
# ==================== DMXAPI 配置 ====================
DMXAPI_BASE_URL=https://www.dmxapi.cn/v1
DMXAPI_API_KEY=your_dmxapi_key_here

# ==================== 默认模型 ====================
DEFAULT_LLM_MODEL=gpt-4o

# ==================== Agent 专属模型（可选） ====================
# Agent 1: 素材理解 - 建议多模态模型（视觉+文本）
MATERIAL_AGENT_MODEL=

# Agent 2: 广告策略 - 建议推理能力强的模型
STRATEGY_AGENT_MODEL=

# Agent 3: 用户洞察 - 建议心理理解强的模型
USER_INSIGHT_AGENT_MODEL=

# Agent 4: 宏观背景 - 建议知识面广的模型
MACRO_AGENT_MODEL=

# Agent 5: 笔记写作 - 建议写作能力最强的模型
NOTE_WRITER_AGENT_MODEL=

# Agent 6: 评分 - 建议结构化输出强的模型
SCORING_AGENT_MODEL=

# ==================== 视觉模型（多模态） ====================
# 用于分析视频帧。如果留空，使用 MATERIAL_AGENT_MODEL
VISION_MODEL=

# ==================== Embedding 模型 ====================
# 用于向量化笔记文本（本地运行，不需要 API）
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIM=384

# ==================== 本地模型配置 ====================
# Whisper 语音转录
WHISPER_MODEL_SIZE=medium        # tiny / base / small / medium / large-v3
WHISPER_DEVICE=cpu               # cpu / cuda
WHISPER_COMPUTE_TYPE=int8        # int8 / float16

# OCR
OCR_ENGINE=tesseract             # tesseract / paddleocr

# ==================== 实时资讯管道 ====================
NEWSBOX_UPDATE_INTERVAL=21600    # 更新间隔（秒），默认 6 小时
NEWSBOX_MAX_SOURCES=10           # 每次最大引用资讯数
NEWSBOX_ENABLED=true             # 是否启用实时资讯

# ==================== 调用参数 ====================
LLM_TIMEOUT=120                  # v0.2 增加超时（视频分析更耗时）
LLM_MAX_RETRIES=1
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# 视觉模型调用参数
VISION_MAX_FRAMES=30             # 单次分析最多使用多少帧
VISION_FRAME_INTERVAL=2          # 每隔几秒抽一帧
```

---

## 模型选择优先级

```
Agent 专属环境变量（如 MATERIAL_AGENT_MODEL）
    ↓ 如果未设置
DEFAULT_LLM_MODEL
    ↓ 如果未设置
gpt-4o（硬编码兜底）

视觉模型：
VISION_MODEL → MATERIAL_AGENT_MODEL → DEFAULT_LLM_MODEL → gpt-4o
```

### Python 配置逻辑（v0.2 增强）

```python
import os

AGENT_MODEL_MAP = {
    "material": "MATERIAL_AGENT_MODEL",
    "strategy": "STRATEGY_AGENT_MODEL",
    "user_insight": "USER_INSIGHT_AGENT_MODEL",
    "macro": "MACRO_AGENT_MODEL",
    "note_writer": "NOTE_WRITER_AGENT_MODEL",
    "scoring": "SCORING_AGENT_MODEL",
}

def get_agent_model(agent_name: str) -> str:
    env_key = AGENT_MODEL_MAP.get(agent_name)
    if env_key:
        model = os.getenv(env_key)
        if model:
            return model
    return os.getenv("DEFAULT_LLM_MODEL", "gpt-4o")

def get_vision_model() -> str:
    return (
        os.getenv("VISION_MODEL")
        or os.getenv("MATERIAL_AGENT_MODEL")
        or os.getenv("DEFAULT_LLM_MODEL")
        or "gpt-4o"
    )
```

---

## v0.2 Agent 模型建议

| Agent | 能力要求 | 首选模型 | 备选 |
|-------|---------|---------|------|
| 素材理解 | 多模态（视觉+文本） | GPT-4o / Gemini-Pro | Claude Sonnet + 单独的视觉模型 |
| 广告策略 | 推理 + 营销知识 | Claude Opus / GPT-4o | DeepSeek-R1 |
| 用户洞察 | 消费心理学 | Claude Sonnet / GPT-4o | DeepSeek-V3 |
| 宏观背景 | 知识面广 + 实时资讯处理 | Claude Opus / GPT-4o | Gemini-Pro |
| 笔记写作 | 中文写作 + 风格控制 | Claude Sonnet / GPT-4o | DeepSeek-R1 |
| **评分（新）** | **结构化输出 + 一致性** | **GPT-4o / Claude Sonnet** | DeepSeek-V3 |

### 成本优化建议（v0.2）

| 层级 | Agent | 建议模型档次 |
|------|-------|------------|
| 贵但值 | 笔记写作、评分 | 最好的模型 |
| 中档 | 策略、用户洞察 | 次好模型 |
| 可省 | 素材理解（文本部分） | 性价比模型 |
| 本地免费 | 语音转录、OCR、Embedding | 本地模型 |

---

## DMXAPI 视觉模型调用约定

```python
# 多模态调用（带图片）
response = await client.chat.completions.create(
    model=get_vision_model(),
    messages=[
        {"role": "system", "content": agent_system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请分析以下视频帧：\n{context}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_frame}"}},
                # ... 多个帧
            ],
        },
    ],
    max_tokens=4096,
)
```

---

## 本地模型下载（首次启动）

```bash
# Whisper 模型（首次使用时自动下载）
# 模型大小：tiny(150MB) / base(300MB) / small(1GB) / medium(3GB) / large(6GB)

# Embedding 模型（首次使用时自动下载）
# paraphrase-multilingual-MiniLM-L12-v2: ~500MB
```

---

## 安全要求（同 v0.1）

1. 不读取真实 .env 文件
2. 不打印 API Key
3. 不写死真实 Key
4. .env.example 用占位符
5. .gitignore 排除 .env
