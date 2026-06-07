# CHANGELOG

---

## v0.3.0-dev (2026-06-07) — Link-only workflow

- 首页改为单一分享口令入口，识别 URL 后自动创建分析任务
- 新增持久化 Job 状态、缺失信息确认和失败重试接口
- 抖音原生解析器提取 CDN 播放地址，绕过 `yt-dlp` cookie 限制
- 视频下载、Whisper 转录、场景抽帧正式接入主分析链路
- 关键帧使用 ffmpeg `pts_time` 记录真实时间戳
- 新增抖音图文、60-90 秒口播、小红书适配稿
- 新增洞察、抖音、小红书三个独立成果页面
- 前端改为广告研究编辑部视觉系统
- 稿件复制增加无 Clipboard API 权限时的降级方案

## v0.2.0 (2026-06-07) — 设计阶段

### 🤖 Epic 3: 真实 LLM 接入 (2026-06-07)

- **新增** `backend/app/llm_client.py` — OpenAI 兼容异步 HTTP 客户端（httpx），支持文本 + 视觉调用，自动重试，截断 JSON 修复
- **新增** `backend/app/agent_pipeline.py` — 6 Agent 真实 LLM 管线，每个 Agent 独立系统提示词 + JSON 结构化输出
- **新增** `.env` 配置 — DMXAPI API Key + 模型选择（视觉 `gpt-5.4-nano` + 文本 `claude-haiku-4-5-20251001`）
- **Agent 5 拆分**：元数据 JSON + Markdown 纯文本双调用，避免长文本 JSON 转义问题
- **Agent 6 评分**：紧凑 JSON 输出，100 字内评分说明，防截断
- **路由更新**：`analyze_ad` 端点自动检测 LLM 配置，有 Key 走真实管线，无 Key 降级 Mock
- **依赖**: httpx, python-dotenv

### 📐 设计文档全面更新

基于 GitHub 同类项目调研（claude-ads、Creative Tagger、SeekMoney-ai 等 7 个项目），重新设计了系统架构。

### 新增

- **六层管道架构**：内容抓取 → 多媒体理解 → 实时资讯 → Agent 分析 → 知识库 → 输出
- **视频链接输入**：粘贴链接自动解析（douyin-mcp + yt-dlp）
- **多模态内容理解**：Whisper 语音转录 + ffmpeg 抽帧 + OCR
- **实时资讯管道**：newsbox 集成，为宏观分析提供 X/新闻/RSS 数据
- **28 维度评分体系**：参考 Creative Tagger，每个广告有量化评分
- **Agent 6（评分 Agent）**：独立的评分和创意 DNA 提取
- **FAISS 知识库**：向量搜索 + Swipe File + Gap Analysis
- **UI 重设计计划**：使用 ui-ux-pro-max-skill

### 变更

| 文件 | 变更 |
|------|------|
| `docs/PRD.md` | 重写为 v0.2，新增视频链接、评分、Swipe File |
| `docs/ARCHITECTURE.md` | 重写为六层管道架构 |
| `docs/AGENT_WORKFLOW.md` | 新增 Agent 6、28 维度评分、实时资讯 |
| `docs/API.md` | 新增解析链接、Swipe File、评分、搜索接口 |
| `docs/DATABASE.md` | 新增 swipe_tags、live_intel_cache、embeddings 表 |
| `docs/LLM_CONFIG.md` | 新增视觉模型、Embedding、Whisper 配置 |
| `docs/TASKS.md` | 重写为 v0.2 开发计划（5 个 Epic） |
| `README.md` | 更新架构总结、参考项目列表 |

### 🎨 UI 重设计 (Epic 8 完成)

Tailwind CSS v4 "Editorial Swiss" 设计系统全面重写前端。

- **Epic 8.1**: 安装 Tailwind CSS v4.3.0 + @tailwindcss/postcss，创建全局设计 Token（colors, typography, spacing, shadows）
- **Epic 8.2**: 重写 `layout.tsx` — sticky header + backdrop-blur，干净导航
- **Epic 8.3**: 重写 `AdForm.tsx` — 链接输入占位 + 可折叠手动表单
- **Epic 8.4**: 重写 `AnalysisResult.tsx`、`MarkdownPreview.tsx`、`ads/[id]/page.tsx` — 四状态分析流程（pending/analyzing/failed/completed）、进度条骨架、统一按钮体系
- **Epic 8.5**: 重写 `ads/page.tsx` — 骨架加载态、状态标签颜色体系、一键洞察预览
- **Epic 8.6**: 全量构建通过，零错误

### 参考项目

| 项目 | 借鉴内容 |
|------|---------|
| claude-ads (5.3k stars) | 广告评分 0-100 + 多维度拆解 |
| Creative Tagger | 28 维度分类法标准化 |
| SeekMoney-ai | 多平台链接解析方案 |
| Meta Ads Pipeline | FAISS 向量搜索知识库 |
| video-link-pipeline | 视频下载 + Whisper 转录管线 |
| newsbox | 52 源实时资讯管道 |
| viral2viral | 创意 DNA 提取思路 |
| Competitor Ads Analyst | Swipe File + Gap Analysis 概念 |

---

## v0.1.0 (2026-06-06) — Mock MVP

### 完成

- [x] 项目脚手架（FastAPI + Next.js + SQLite）
- [x] 7 个 REST API 端点
- [x] Mock Agent Pipeline（5 个 Agent 模拟分析）
- [x] 前端 3 个页面（录入表单、详情、历史列表）
- [x] Markdown 笔记渲染和导出
- [x] `.env.example` 模板

### 文件清单

```
backend/
  app/
    main.py              # FastAPI 入口
    database.py           # SQLite 初始化
    schemas.py            # Pydantic 模型
    mock_pipeline.py      # Mock 5-Agent 管道
    routers/
      ads.py              # 7 个 API 端点
  requirements.txt

frontend/
  app/
    page.tsx              # 首页（AdForm）
    layout.tsx            # 全局布局
    ads/
      page.tsx            # 历史列表
      [id]/page.tsx       # 详情 + 分析
  components/
    AdForm.tsx            # 广告录入表单
    MarkdownPreview.tsx   # Markdown 渲染
    AnalysisResult.tsx    # 分析结果
  lib/
    api.ts                # API 客户端
  package.json

.env.example
.gitignore
README.md
docs/
  PRD.md
  ARCHITECTURE.md
  AGENT_WORKFLOW.md
  API.md
  DATABASE.md
  LLM_CONFIG.md
  TASKS.md
```

### 已知限制

- [ ] Mock 模式，未接入真实 LLM
- [ ] API 导出中文文件名编码问题（已修复）
- [ ] npm install 在 npmmirror 下可能因 SSL 证书问题卡住（需 `npm config set strict-ssl false`）
- [x] UI 为基础样式，未使用设计系统

---

## v0.2.0-dev (2026-06-07) — 链接解析

### 🔗 Epic 9: 视频链接解析

- **新增** `POST /api/parse-link` 端点 — 粘贴链接自动解析视频元数据
- **新增** `backend/services/link_parser.py` — 统一解析服务，yt-dlp 作为解析引擎
- **平台识别**: 自动检测 6+ 平台（抖音、TikTok、小红书、B站、快手、YouTube、视频号）
- **前端联动**: AdForm 链接输入框已启用，解析后自动填充表单
- **依赖**: yt-dlp 2026.3.17

### 🏆 Agent 6 评分系统

- **新增** `_build_scoring()` Mock 评分管线 — 20 维度 7 大类评分 (hook/messaging/trust/conversion/emotion/production/innovation)
- **加权计算**: 钩子 20% / 信息传递 20% / 转化 20% / 情绪 15% / 信任 10% / 制作 10% / 创新 5%
- **评分等级**: S/A/B/C/D 五级，带颜色标识
- **创意 DNA 提取**: 叙事模板、情绪公式、钩子结构、可复用元素
- **Swipe 标签**: 自动生成 #行业 #平台 #钩子 #价格 #信任 #评分 #品牌 标签
- **前端 ScoreCard 组件**: 环形分数、分类进度条、创意 DNA、标签云

### 🎨 Swipe File 页面

- **新增** `/swipe` 页面 — 灵感库卡片网格展示已完成分析的广告
- **筛选**: 按行业(9) × 平台(5) × 搜索词过滤
- **卡片**: 品牌/产品/洞察/标签，点击跳转详情页
- **导航**: layout 新增 Swipe File 入口

### 📋 当前状态 (2026-06-07)

**已完工:**
- ✅ v0.1 Mock MVP 全部功能
- ✅ UI 重设计（Tailwind v4 Editorial Swiss）
- ✅ 视频链接解析（yt-dlp + 6+ 平台识别 + 前端联动）
- ✅ Agent 6 评分系统（20 维度 + 创意 DNA + Swipe 标签）
- ✅ ScoreCard 前端组件 + `/swipe` 灵感库页面

**待后续（需外部依赖或用户操作）:**
| 项目 | 阻塞原因 |
|------|---------|
| Epic 10: 多媒体理解 | ✅ 完成（ffmpeg + faster-whisper + 关键帧） |
| Epic 11: 实时资讯 | 需配置 newsbox 服务 |
| Epic 3: 真实 LLM | 需 DMXAPI Key |
| FAISS 知识库 | 需 sentence-transformers |
| 端到端测试 | 依赖以上模块 |

### 🎬 Epic 10: 多媒体理解 (2026-06-07)

- **新增** `services/frame_extractor.py` — ffmpeg 场景检测 + 统一采样关键帧提取
- **新增** `services/transcriber.py` — faster-whisper medium 模型语音转录（中文为主，支持 auto-detect）
- **新增** `services/ocr.py` — 帧预处理 + base64 导出（为 Vision LLM 分析做准备）
- **新增** `services/media_pipeline.py` — 统一管线：下载 → 抽帧 → 转录 → 导出
- **新增** `POST /api/analyze-media` 端点
- **依赖**: faster-whisper 1.2.1（medium 模型 ~1.8GB，缓存于 `~/.cache/faster-whisper/`）
