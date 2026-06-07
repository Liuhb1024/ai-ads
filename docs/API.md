# API — 后端接口设计 v0.2

> 版本: v0.2.0  
> 更新: 2026-06-07

---

## v0.1 → v0.2 新增接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/parse-link` | 解析视频链接，返回元数据 |
| GET | `/api/swipe` | Swipe File 灵感库列表 |
| GET | `/api/swipe/search` | 语义搜索历史笔记 |
| GET | `/api/swipe/gap-analysis` | 品类内容缺口分析 |
| GET | `/api/ads/{id}/score` | 获取单条广告的 28 维度评分 |

---

## 接口详细设计

### 1. 解析视频链接（新增）

```
POST /api/parse-link
```

**Request**
```json
{
  "url": "https://v.douyin.com/xxxxx/",
  "platform_hint": "抖音"  // 可选，帮助选择解析器
}
```

**Response 200（解析成功）**
```json
{
  "status": "success",
  "platform": "抖音",
  "metadata": {
    "title": "还在为颈纹焦虑？试试这个",
    "author": "欧莱雅官方旗舰店",
    "description": "28天淡化颈纹...",
    "duration_seconds": 45,
    "like_count": 12000,
    "comment_count": 380,
    "share_count": 2500,
    "cover_url": "https://..."
  },
  "video_downloaded": true,
  "transcript_available": true
}
```

**Response 200（部分成功）**
```json
{
  "status": "partial",
  "platform": "抖音",
  "metadata": {
    "title": "还在为颈纹焦虑？试试这个",
    "author": "欧莱雅官方旗舰店"
  },
  "video_downloaded": false,
  "error": "视频下载被平台限制，建议手动补充画面描述",
  "fallback_to_manual": false
}
```

**Response 422（解析失败）**
```json
{
  "status": "failed",
  "error": "无法解析此链接",
  "suggestion": "请使用手动填写模式",
  "fallback_to_manual": true
}
```

---

### 2. 创建广告记录（增强）

```
POST /api/ads
```

v0.2 新增字段：

```json
{
  "source_url": "https://v.douyin.com/xxxxx/",
  "parse_result": { /* /api/parse-link 的返回值 */ },
  "use_live_intel": true,
  // ... v0.1 所有字段保留，作为 fallback
}
```

---

### 3. 分析进度 SSE（增强）

新增阶段事件：

```
event: stage_start
data: {"stage": 1, "name": "content_fetch", "message": "正在获取视频内容..."}

event: stage_start
data: {"stage": 2, "name": "media_understanding", "message": "正在转录语音 + 分析画面..."}

event: stage_start  
data: {"stage": 3, "name": "live_intel", "message": "正在获取实时资讯..."}

event: stage_start
data: {"stage": 4, "name": "agent_pipeline", "agent": 1, "message": "Agent 1/6: 素材理解..."}

event: stage_start
data: {"stage": 5, "name": "knowledge_base", "message": "正在入库到 Swipe File..."}
```

---

### 4. Swipe File 列表（新增）

```
GET /api/swipe?industry=美妆&tag=钩子_痛点直击&sort=score&limit=20&offset=0
```

**Response 200**
```json
{
  "total": 42,
  "items": [
    {
      "id": "a1b2c3d4",
      "brand_name": "欧莱雅",
      "product_name": "复颜玻尿酸颈霜",
      "platform": "抖音",
      "thumbnail_url": "...",
      "overall_score": 72,
      "hook_type": "痛点直击型",
      "tags": ["#钩子_痛点直击", "#情绪_焦虑转希望", "#行业_美妆"],
      "one_sentence_takeaway": "...",
      "created_at": "2026-06-07T10:30:00"
    }
  ]
}
```

---

### 5. 语义搜索（新增）

```
GET /api/swipe/search?q=钩子很强+美妆+焦虑&limit=10
```

**Response 200**
```json
{
  "query": "钩子很强 美妆 焦虑",
  "results": [
    {
      "id": "a1b2c3d4",
      "similarity": 0.92,
      "brand_name": "欧莱雅",
      "one_sentence_takeaway": "...",
      "tags": ["..."]
    }
  ]
}
```

---

### 6. Gap Analysis（新增）

```
GET /api/swipe/gap-analysis?industry=美妆
```

**Response 200**
```json
{
  "industry": "美妆",
  "analyzed_count": 15,
  "dimension_coverage": {
    "hook_types": {
      "used": ["痛点直击型", "效果承诺型", "好奇心缺口型"],
      "unused": ["反常识型", "身份认同型", "数据震撼型"],
      "gap_opportunity": "「反常识型钩子」在美妆品类中很少见，可以尝试"
    },
    "emotions": {
      "used": ["焦虑", "希望", "自信"],
      "unused": ["幽默", "愤怒", "怀旧"],
      "gap_opportunity": "美妆广告几乎没人用幽默，如果你的品牌调性合适，可以试试"
    }
  }
}
```

---

### 7. 评分查询（新增）

```
GET /api/ads/{id}/score
```

**Response 200**
```json
{
  "analysis_id": "a1b2c3d4",
  "overall_score": 72,
  "dimensions": {
    "hook": {"hook_type": 4, "opening_impact": 5, "curiosity_gap": 3},
    "messaging": {"usp_clarity": 4, "claim_credibility": 3, "differentiation": 3},
    "trust": {"endorsement_strength": 2, "social_proof": 3, "data_backing": 2},
    "conversion": {"cta_clarity": 4, "urgency": 3, "low_barrier": 4},
    "emotion": {"emotional_intensity": 4, "emotional_precision": 5, "resonance": 4},
    "production": {"visual_quality": 3, "audio_quality": 3, "pacing": 4},
    "innovation": {"creative_freshness": 2, "category_breakthrough": 2}
  },
  "creative_dna": { /* ... */ },
  "swipe_tags": ["#钩子_痛点直击", "..."]
}
```

---

## 完整接口列表（v0.2）

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | `/api/health` | 健康检查 | v0.1 |
| POST | `/api/parse-link` | 解析视频链接 | **v0.2** |
| POST | `/api/ads` | 创建广告记录 | v0.1+ |
| GET | `/api/ads` | 历史列表 | v0.1 |
| GET | `/api/ads/{id}` | 查询详情 | v0.1 |
| POST | `/api/ads/{id}/analyze` | 触发分析 | v0.1 |
| GET | `/api/ads/{id}/progress` | SSE 进度 | v0.1+ |
| GET | `/api/ads/{id}/analysis` | 分析结果 | v0.1 |
| GET | `/api/ads/{id}/score` | 28 维度评分 | **v0.2** |
| GET | `/api/ads/{id}/export.md` | 导出 Markdown | v0.1 |
| DELETE | `/api/ads/{id}` | 删除记录 | v0.1 |
| GET | `/api/swipe` | Swipe File 列表 | **v0.2** |
| GET | `/api/swipe/search` | 语义搜索 | **v0.2** |
| GET | `/api/swipe/gap-analysis` | 缺口分析 | **v0.2** |

---

## 当前自动任务接口（已实现）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/jobs` | 接收完整分享口令，自动提取 URL 并创建后台分析任务 |
| GET | `/api/jobs/{id}` | 获取持久化阶段、缺失字段、洞察和发布稿 |
| PATCH | `/api/jobs/{id}/metadata` | 补齐缺失的品牌、产品、行业并继续分析 |
| POST | `/api/jobs/{id}/retry` | 重试失败任务 |
| GET | `/api/jobs/{id}/export.md` | 下载结构化专业 Markdown 报告 |
| GET | `/api/jobs/{id}/export.pdf` | 下载同版式 PDF 报告 |

`POST /api/jobs` 请求：

```json
{
  "share_text": "抖音完整分享文案 https://v.douyin.com/xxxx/ 复制打开抖音"
}
```

任务完成后：

- `analysis.analysis_meta` 记录视频模型、素材模式、证据数量和审查结果。
- `analysis.material_understanding.evidence_ledger` 包含时间戳证据。
- `analysis.quality_audit` 包含批准/驳回 Claim ID、限制和可信度分数。
- `publishing` 包含 `douyin_article`、`douyin_script`、`xiaohongshu` 和双候选评审元数据。
