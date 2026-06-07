# DATABASE — 数据库设计 v0.2

> 版本: v0.2.0  
> 数据库: SQLite + FAISS  
> 更新: 2026-06-07

---

## v0.1 → v0.2 变化

| 变化 | 说明 |
|------|------|
| ads 表新增字段 | source_url, source_platform, video_path, transcript_path, score_json, creative_dna_json, embedding_id |
| 新增 swipe_tags 表 | 标签体系，支撑 Swipe File 分类和筛选 |
| 新增 live_intel_cache 表 | 实时资讯缓存，减少重复抓取 |
| 新增 embeddings 元数据表 | FAISS 索引的映射关系 |
| FAISS 索引文件 | `backend/data/embeddings.faiss`（二进制） |

---

## 表结构

### 1. ads — 分析记录主表（增强）

```sql
CREATE TABLE ads (
    id          TEXT PRIMARY KEY,

    -- v0.2 新增：视频来源
    source_url        TEXT,
    source_platform   TEXT,           -- 抖音/小红书/视频号/TikTok/B站/YouTube
    video_path        TEXT,           -- 下载的视频文件路径
    video_downloaded  INTEGER DEFAULT 0,
    transcript_path   TEXT,           -- Whisper 转录文本路径
    transcript_status TEXT,           -- pending/completed/failed

    status      TEXT NOT NULL DEFAULT 'pending',

    -- v0.1 字段（保留，作为 fallback）
    ad_title            TEXT,
    brand_name          TEXT NOT NULL,
    product_name        TEXT,
    industry            TEXT NOT NULL,
    price_range         TEXT,
    ad_copy             TEXT,
    scene_description   TEXT,
    screenshot_description TEXT,
    user_context        TEXT,
    seen_at             TEXT,
    platform            TEXT NOT NULL,

    -- 分析结果
    analysis_json       TEXT,

    -- v0.2 新增：评分和创意 DNA
    score_json          TEXT,          -- Agent 6 的 28 维度评分
    creative_dna_json   TEXT,          -- 创意 DNA 提取结果
    swipe_tags          TEXT,          -- JSON 数组：["#钩子_痛点直击", "#行业_美妆"]

    -- v0.2 新增：实时资讯
    live_intel_used     INTEGER DEFAULT 0,
    live_intel_sources  TEXT,          -- JSON：[{"source": "X", "relevance": 0.85}]

    -- v0.2 新增：向量索引
    embedding_id        TEXT,          -- FAISS 索引 ID
    embedding_status    TEXT DEFAULT 'pending',  -- pending/completed/failed

    -- 错误信息
    error_message       TEXT,
    failed_stage        TEXT,          -- v0.2：content_fetch/media_understanding/live_intel/agent_pipeline/knowledge_base

    -- 时间戳
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
    analyzed_at  TEXT
);
```

### 2. swipe_tags — 标签字典

```sql
CREATE TABLE swipe_tags (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE,     -- "#钩子_痛点直击"
    category TEXT NOT NULL,           -- hook/emotion/narrative/industry/platform/style/score_range
    usage_count INTEGER DEFAULT 0
);

-- 预置标签
INSERT INTO swipe_tags (name, category) VALUES
    -- 钩子类型
    ('#钩子_痛点直击', 'hook'),
    ('#钩子_效果承诺', 'hook'),
    ('#钩子_好奇心缺口', 'hook'),
    ('#钩子_反常识', 'hook'),
    ('#钩子_身份认同', 'hook'),
    ('#钩子_数据震撼', 'hook'),
    ('#钩子_价格冲击', 'hook'),
    ('#钩子_视觉冲击', 'hook'),
    -- 情绪
    ('#情绪_焦虑转希望', 'emotion'),
    ('#情绪_恐惧转安全', 'emotion'),
    ('#情绪_自卑转自信', 'emotion'),
    ('#情绪_好奇转满足', 'emotion'),
    ('#情绪_愤怒转正义', 'emotion'),
    ('#情绪_怀旧', 'emotion'),
    ('#情绪_幽默', 'emotion'),
    -- 叙事结构
    ('#叙事_问题解决', 'narrative'),
    ('#叙事_前后对比', 'narrative'),
    ('#叙事_创始人故事', 'narrative'),
    ('#叙事_素人分享', 'narrative'),
    ('#叙事_专家讲解', 'narrative'),
    ('#叙事_第三方案例', 'narrative'),
    -- 评分区间
    ('#评分_80以上', 'score_range'),
    ('#评分_60-80', 'score_range'),
    ('#评分_60以下', 'score_range');
```

### 3. live_intel_cache — 实时资讯缓存

```sql
CREATE TABLE live_intel_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT NOT NULL,        -- X/Reddit/RSS/News
    headline        TEXT NOT NULL,
    url             TEXT,
    content_snippet TEXT,
    published_at    TEXT,
    fetched_at      TEXT NOT NULL DEFAULT (datetime('now')),
    relevance_tags  TEXT,                 -- JSON：["美妆", "618", "消费"]
    relevance_score REAL,                 -- 缓存时预计算的相关性
    expires_at      TEXT                  -- 过期时间
);

CREATE INDEX idx_live_intel_tags ON live_intel_cache(relevance_tags);
CREATE INDEX idx_live_intel_fetched ON live_intel_cache(fetched_at DESC);
```

### 4. embeddings — FAISS 索引映射

```sql
CREATE TABLE embeddings (
    id          TEXT PRIMARY KEY,         -- FAISS 索引 ID
    analysis_id TEXT NOT NULL REFERENCES ads(id) ON DELETE CASCADE,
    dim         INTEGER NOT NULL,         -- 向量维度（如 768）
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## FAISS 索引

### 文件位置

```
backend/data/embeddings.faiss        # FAISS 索引文件
backend/data/embeddings_meta.json    # 元数据映射（id → analysis_id）
```

### 索引参数

```python
import faiss

dimension = 768  # sentence-transformers 输出维度
index = faiss.IndexFlatIP(dimension)  # 内积相似度（余弦相似度的等价）
# 或使用 IndexHNSWFlat 加速大规模搜索
```

---

## 示例数据

### ads 表示例行（v0.2 新增字段）

```
source_url: https://v.douyin.com/xxxxx/
source_platform: 抖音
video_path: uploads/videos/a1b2c3d4.mp4
transcript_path: uploads/transcripts/a1b2c3d4.txt
transcript_status: completed
score_json: {"overall_score": 72, "dimensions": {...}}
creative_dna_json: {"narrative_template": "问题-认同-方案-证明-行动", ...}
swipe_tags: ["#钩子_痛点直击", "#情绪_焦虑转希望", "#叙事_问题解决", "#行业_美妆", "#评分_70以上"]
embedding_id: emb_0001
embedding_status: completed
live_intel_used: 1
live_intel_sources: [{"source": "X/Twitter", "headline": "618美妆预售数据...", "relevance": 0.85}]
```

---

## 数据清理策略

| 数据 | 清理策略 |
|------|---------|
| 视频文件 | 分析完成后 7 天自动删除（可选保留） |
| 转录文本 | 保留，不占空间 |
| 实时资讯缓存 | 72 小时过期自动删除 |
| FAISS 索引 | 增量更新，不删除 |
| 分析记录 | 不自动删除，用户手动删 |
