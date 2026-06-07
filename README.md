# ai-ad — 短视频广告洞察与自媒体成稿工具

> 粘贴完整分享口令 → 自动看视频 → AI 拆解 → 抖音图文/口播 + 小红书版本

---

## 这是什么

ai-ad 帮你把刷到的广告视频变成：
1. **一篇可审计的创意研究报告**（事实、推断、假设分层，带时间戳证据）
2. **证据锚定的量化评分**（每个类别附评分理由和证据编号）
3. **个人 Swipe File**（积累你的广告灵感库，可搜索、可筛选）
4. **可直接编辑发布的内容包**（抖音图文、60-90 秒口播稿、小红书适配稿）
5. **一键导出 Markdown / PDF**（网页、MD、PDF 使用同一份报告结构）

## 当前主流程

1. 在首页粘贴平台完整分享口令或直接链接。
2. 系统自动提取 URL、解析元数据、下载视频、Whisper 转录并抽取关键帧。
3. 自动识别品牌、产品和行业；只有缺失时才显示极简确认页。
4. 使用 `doubao-seed-2-0-lite-260215` 优先理解完整视频，失败时降级到关键帧和文本。
5. 运行证据提取、策略、人群、语境、事实审查、评分和编辑 Agent。
6. 生成两套发布候选，通过正反顺序成对评审选择最终稿。
7. 分页查看洞察报告、抖音成稿和小红书版本，并导出 MD/PDF。

当前抖音链接优先使用页面内嵌播放地址，避免 `yt-dlp` 对新鲜 cookies 的依赖。

参考了 GitHub 上 claude-ads (5.3k stars)、Creative Tagger、SeekMoney-ai 等项目的设计思路。

---

## 当前版本

**v0.3 — 证据驱动的完整视频分析** ✅

| 状态 | 内容 |
|------|------|
| ✅ | 分享口令自动解析、下载、转写和关键帧提取 |
| ✅ | 豆包完整视频主链路与关键帧/文本降级 |
| ✅ | 时间戳证据账本、Claim ID、独立审查和可信度校准 |
| ✅ | 抖音主稿、小红书适配稿、双候选反向评审 |
| ✅ | 专业报告页面、Markdown 和 PDF 导出 |

---

## 重要说明

| 维度 | Claude Code（开发用） | ai-ad 项目 Agent（运行时） |
|------|---------------------|--------------------------|
| 模型 | deepseek-v4-pro | 通过 DMXAPI 配置 |
| 用途 | 写 ai-ad 的代码 | 分析广告、生成笔记 |
| 费用 | Claude Code 订阅 | DMXAPI 账户 |

---

## 本地启动（v0.1 当前可用）

### 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs
```

### 前端

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3001
```

### 测试

```bash
# 创建广告
curl -X POST http://localhost:8000/api/ads \
  -H "Content-Type: application/json" \
  -d '{"brand_name":"欧莱雅","industry":"美妆","platform":"抖音"}'

# 触发分析
curl -X POST http://localhost:8000/api/ads/{id}/analyze

# 导出
curl -O http://localhost:8000/api/jobs/{id}/export.md
curl -O http://localhost:8000/api/jobs/{id}/export.pdf
```

---

## 目录结构

```
ai-ad/
├── docs/                   # 设计文档（v0.2 更新）
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── AGENT_WORKFLOW.md
│   ├── API.md
│   ├── DATABASE.md
│   ├── LLM_CONFIG.md
│   ├── TASKS.md
│   └── CHANGELOG.md
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── mock_pipeline.py
│   │   ├── schemas.py
│   │   └── routers/ads.py
│   ├── data/               # SQLite
│   ├── exports/
│   └── requirements.txt
├── frontend/               # Next.js 前端
│   ├── app/
│   ├── components/
│   └── lib/
├── .env.example
└── README.md
```

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
| 开发计划 | [TASKS.md](./docs/TASKS.md) |
| 变更记录 | [CHANGELOG.md](./docs/CHANGELOG.md) |

---

## 设计参考

本项目设计思路参考了以下开源项目：

- [claude-ads](https://github.com/AgriciDaniel/claude-ads) — 广告质量评分体系
- [Creative Tagger](https://pypi.org/project/creative-tagger/) — 28 维度创意分类法
- [SeekMoney-ai](https://github.com/liangdabiao/SeekMoney-ai) — 多平台采集 + 语义聚类
- [Meta Ads Pipeline](https://github.com/AdvaySanketi/Meta-Ads-Project) — FAISS 向量搜索
- [video-link-pipeline](https://github.com/xiexikang/video-link-pipeline) — 多平台视频处理
- [newsbox](https://pypi.org/project/newsbox/) — 52 源实时资讯管道

---

## 安全声明

- `.env.example` 不含真实 API Key
- 不读取真实 `.env`
- 不爬取平台
- Mock 模式不产生外部调用

---

## License

MIT
