# ai-ad — 证据驱动的短视频广告创意智能分析引擎

> 粘贴分享口令 → AI 拆解广告 → 生成抖音/小红书发布稿 → 积累个人 Swipe File
>
> 每天分析一条广告，把创意方法论讲给更多人听。

---

## 项目蓝图

**这不是一个 SaaS 工具，这是一个内容创作引擎。**

核心理念：每天分析一条广告，将 AI 拆解结果做成有洞察的内容，发布到抖音和小红书。通过持续输出"广告背后的原理"，启发创业者、职场人，也启发自己。

### 三层架构

```
┌──────────────────────────────────────────────────────────────┐
│                    输入层 — 多平台广告采集                      │
│  粘贴分享口令 → 解析链接 → 下载视频 → Whisper 转录 → 关键帧提取  │
│  支持: 抖音 | 小红书 | 快手 | 视频号                            │
└─────────────────────────┬────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    分析层 — 7 Agent 证据账本流水线               │
│                                                               │
│  Agent 1           Agent 2        Agent 3        Agent 4     │
│  素材理解 ────────→ 广告策略 ────→ 用户洞察 ────→ 宏观语境     │
│  (视频证据提取)     (策略推演)     (人群定位)     (行业背景)     │
│                                                               │
│  Agent 5           Agent 6        Agent 7                     │
│  事实性审查 ──────→ 锚定评分 ────→ 编辑元数据                   │
│  (独立审计)         (量化评估)     (标题/金句/标签)              │
│                                                               │
│  核心方法论: 每个结论附带证据编号和时间戳，事实与推断分层          │
└─────────────────────────┬────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    输出层 — 多平台发布                           │
│                                                               │
│  双候选生成 → 正反顺序成对评审 → 选择最佳稿 → 低分自动修订       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ 抖音图文  │  │ 口播脚本  │  │ 小红书稿  │                    │
│  └──────────┘  └──────────┘  └──────────┘                    │
│  → Markdown / PDF 一键导出                                     │
└──────────────────────────────────────────────────────────────┘
```

### 后续规划：视频生产链路

当前阶段（v0.3）完成的是"分析能力"和"发布稿生成"。下一步是将分析结果自动制成视频内容（如 PPT 式讲解视频），直接在抖音/小红书发布。

---

## 核心特性

### 证据账本方法论
每个分析结论都标注证据来源（时间戳 + 模态），区分"素材中明确出现的"和"模型推断的"，经过独立事实性审查（Critical ×5.0 / Major ×3.0 严重性乘数）。

### 13 种 Hook 模式分类
基于 LazyReel 方法论，强制从 POV 代入、信念挑战、直接点名、信息缺口、结果前置等 13 种模式中选择，让钩子分析一致、可跨广告对比。

### 7 维度创意评分
钩子 (20%) + 信息传递 (20%) + 转化设计 (20%) + 情绪调动 (15%) + 信任建立 (10%) + 制作水准 (10%) + 创新性 (5%)。每个维度附评分理由和证据编号。

### 人类校准
Spearman ρ 秩相关系数（纯 Python 实现，无 scipy 依赖），量化 AI 评分与人类专家判断的一致性。支持专家间信度分析。

### Anti-Slop 质量门
检测 AI 模板化表述（"在当今时代""简直是神器""彻底颠覆"等），超阈值自动回退。出版稿 clarity/actionability < 7 分时自动修订一轮。

### 语义搜索
sentence-transformers + FAISS 向量索引，按语义检索历史广告，积累个人 Swipe File。

### 创意 A/B 对比
两条广告侧面对比，LLM 预测优势方，输出 7 维对比分析。

### 行业差异化模板
美妆、3C、教育、食品、金融、大健康、汽车 7 个行业各有专属分析维度。

---

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 前端 | Next.js 14 (App Router) + Tailwind CSS | 服务端渲染，零运行时 CSS |
| 后端 | FastAPI (Python) | 异步 HTTP，REST API |
| 数据库 | SQLite (aiosqlite) | 零配置，单文件部署 |
| AI 模型 | DMXAPI (DeepSeek/Claude/Doubao) | 多模型路由，vision + video 支持 |
| 视频理解 | Doubao Seed 2.0 Lite | 完整视频优先，关键帧降级 |
| 语音转写 | Whisper (faster-whisper) | 本地 GPU 推理 |
| 向量搜索 | sentence-transformers + FAISS | 多语言语义索引 |
| 视频下载 | yt-dlp | 多平台 fallback |
| 内容压缩 | ModernBERT + kompress-int8 | Headroom proxy 上下文压缩 |

---

## 本地启动

### 环境要求
- Python 3.11+
- Node.js 18+
- FFmpeg（视频处理）

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填写 DMXAPI_API_KEY
```

### 2. 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# API 文档: http://localhost:8000/docs
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3001
```

### 4. 运行测试

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

---

## 使用流程

1. **粘贴分享口令** — 支持抖音、小红书、快手、视频号的完整分享口令或直接链接
2. **自动解析** — 提取视频、转写语音、捕获关键帧
3. **确认元数据** — 品牌/产品/行业缺失时才需要手动补充
4. **AI 分析** — 7 Agent 流水线自动运行，约 2-3 分钟
5. **查看结果** — 洞察报告（证据 + 评分）、抖音成稿、小红书版本
6. **导出** — Markdown / PDF 一键下载

---

## 目录结构

```
ai-ad/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 应用入口
│   │   ├── agent_pipeline.py    # 7 Agent 证据流水线
│   │   ├── publishing_pipeline.py # 出版稿生成 + 双候选评审
│   │   ├── analysis_quality.py  # 质量门禁 + 事实审查
│   │   ├── comparison_engine.py # 创意 A/B 对比引擎
│   │   ├── swipe_index.py       # FAISS 语义搜索索引
│   │   ├── reporting.py         # Markdown 报告生成
│   │   ├── pdf_export.py        # PDF 导出
│   │   ├── llm_client.py        # LLM API 客户端（异步 + 重试）
│   │   ├── database.py          # SQLite 数据库
│   │   ├── schemas.py           # Pydantic 模型
│   │   ├── workflow.py          # Job 工作流编排
│   │   ├── share_text.py        # 分享口令解析
│   │   ├── mock_pipeline.py     # Mock 模式（无 LLM 调试用）
│   │   ├── services/
│   │   │   └── link_parser.py   # 多平台视频链接解析
│   │   └── routers/
│   │       ├── ads.py           # 广告 CRUD + 搜索 + 对比
│   │       ├── jobs.py          # Job 生命周期
│   │       └── calibration.py   # 人类校准 API
│   ├── services/
│   │   └── link_parser.py       # 抖音/小红书/快手/视频号原生解析
│   ├── tests/                   # 45 个测试
│   ├── data/                    # SQLite 数据库文件
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # 首页（分享口令粘贴）
│   │   ├── jobs/[id]/           # Job 进度 + 结果页（insight/douyin/xiaohongshu）
│   │   ├── ads/                 # 广告列表 + 详情
│   │   ├── swipe/               # Swipe File 语义搜索
│   │   ├── compare/             # 创意 A/B 对比
│   │   ├── calibration/         # 人类评分 + 校准报告
│   │   └── layout.tsx
│   ├── components/              # 共享组件（ScoreCard 等）
│   └── lib/api.ts               # API 客户端
├── docs/                        # 设计文档
├── devlog/                      # 开发日志
├── ROADMAP.md                   # 开发路线图
├── SUBSCRIPTIONS.md             # 信息源订阅
└── README.md
```

---

## 路线图

| 阶段 | 状态 | 内容 |
|------|------|------|
| P1 质量护栏 | ✅ | Hook 分类、Anti-Slop、严重性乘数 |
| P2 功能深化 | ✅ | 语义搜索、行业模板、自动修订 |
| P3 验证与壁垒 | ✅ | 人类校准、A/B 对比、多平台解析 |
| P4 视频生产 | 🔜 | PPT 式讲解视频自动生成 |

详见 [ROADMAP.md](./ROADMAP.md)

---

## 文档导航

| 想了解什么 | 文档 |
|-----------|------|
| 产品规划 | [PRD.md](./docs/PRD.md) |
| 系统架构 | [ARCHITECTURE.md](./docs/ARCHITECTURE.md) |
| Agent 设计 | [AGENT_WORKFLOW.md](./docs/AGENT_WORKFLOW.md) |
| API 接口 | [API.md](./docs/API.md) |
| 数据库 | [DATABASE.md](./docs/DATABASE.md) |
| LLM 配置 | [LLM_CONFIG.md](./docs/LLM_CONFIG.md) |
| 变更记录 | [CHANGELOG.md](./docs/CHANGELOG.md) |
| 开发日志 | [devlog/](./devlog/) |

---

## 设计参考

- [claude-ads](https://github.com/AgriciDaniel/claude-ads) — 广告质量评分体系
- [Creative Tagger](https://pypi.org/project/creative-tagger/) — 28 维度创意分类法
- [SeekMoney-ai](https://github.com/liangdabiao/SeekMoney-ai) — 多平台采集 + 语义聚类
- [Meta Ads Pipeline](https://github.com/AdvaySanketi/Meta-Ads-Project) — FAISS 向量搜索
- [video-link-pipeline](https://github.com/xiexikang/video-link-pipeline) — 多平台视频处理
- [newsbox](https://pypi.org/project/newsbox/) — 52 源实时资讯管道

---

## License

MIT
