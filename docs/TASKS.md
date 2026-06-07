# TASKS — 开发任务拆解 v0.2

> 版本: v0.2.0  
> 更新: 2026-06-07

---

## v0.1 完成情况回顾

| Epic | 内容 | 状态 |
|------|------|------|
| Epic 1 | 项目脚手架搭建 | ✅ 完成 |
| Epic 2 | 数据模型 & 数据库 | ✅ 完成（v0.1 版本） |
| Epic 3 | LLM 配置层（占位） | ⏳ 占位完成，未接 DMXAPI |
| Epic 4 | Agent 管道（Mock） | ✅ 完成（Mock 模式） |
| Epic 5 | API 路由（v0.1） | ✅ 完成 |
| Epic 6 | 前端（v0.1 基础 UI） | ✅ 完成 |
| Epic 8 | UI 重设计（Editorial Swiss） | ✅ 完成（8.1-8.6） |
| Epic 9 | 视频链接解析 | ✅ 完成 |
| Epic 12 | 评分 + Swipe File | ✅ Mock 版完成 |
| Epic 10 | 多媒体理解（Whisper/ffmpeg/OCR） | ⏳ 待 v0.3 |
| Epic 11 | 实时资讯管道（newsbox） | ⏳ 待 v0.3 |
| Epic 13 | 集成测试 | ⏳ 待 v0.3 |
| Epic 3 | DMXAPI 真实 LLM 接入 | ⏳ 需 API Key |

---

## v0.2 开发计划

### Epic 8: UI 重设计（优先）

**目标**: 使用 UI Design Skill 重做前端，建立品牌视觉。

#### Task 8.1 — 安装并配置 UI Design Skill ✅
**优先级**: P0  
**预估**: 0.5 天  
**描述**: 确定设计方向为 "Editorial Swiss" — 干净排版、宽松留白、中性色板、内容优先。

**验收标准**:
- [x] 设计方向确定为 Editorial Swiss Minimalism
- [x] 色彩系统：stone-50/900 中性色 + ink/paper/accent Token
- [x] 字体方案：Inter + JetBrains Mono + Georgia

#### Task 8.2 — 重做 Layout 和全局样式 ✅
**优先级**: P0  
**预估**: 1 天  
**描述**: 重做 `layout.tsx`、全局 CSS（globals.css）。

**验收标准**:
- [x] Tailwind v4 @theme 全局色彩系统（ink, paper, border, accent, success, warning, danger, highlight）
- [x] 字体系统（sans/mono/serif）
- [x] Header sticky + backdrop-blur 导航重设计
- [x] Base styles: h1-h4, p, a, blockquote, code, table, hr
- [x] 统一间距和圆角规范

#### Task 8.3 — 重做首页（链接输入 + 降级表单） ✅
**优先级**: P0  
**预估**: 1 天  
**描述**: 首页核心交互：粘贴链接 → 自动解析 → 预览确认。表单作为降级方案。

**验收标准**:
- [x] 链接输入框为主视觉焦点（disabled 占位态）
- [x] 手动表单可折叠（"展开手动填写表单"按钮）
- [x] 统一 Tailwind inputClass/labelClass 组件风格
- [x] 明确的视觉层次（链接区 → 折叠按钮 → 表单 → 提交）

#### Task 8.4 — 重做分析结果页 ✅
**优先级**: P0  
**预估**: 1 天  
**描述**: 笔记渲染页 + 评分卡片 + 操作按钮。

**验收标准**:
- [x] 洞察一句话 amber callout 卡片
- [x] Markdown 笔记排版使用 globals.css base styles
- [x] 复制/下载/重新分析按钮统一设计
- [x] 四状态流程：pending（CTA）→ analyzing（进度条）→ failed（重试）→ completed（笔记）
- [x] 加载骨架屏动画

#### Task 8.5 — 新建 Swipe File 页
**优先级**: P1  
**预估**: 1 天  
**描述**: Swipe File 灵感库，卡片网格 + 筛选 + 搜索。（v0.2 后续开发）

**验收标准**:
- [ ] 卡片网格展示历史笔记摘要
- [ ] 按行业/钩子/情绪/评分筛选
- [ ] 语义搜索框
- [ ] 点击卡片跳转详情

#### Task 8.6 — 移动端适配 ✅
**优先级**: P1  
**预估**: 0.5 天  
**描述**: 确保在手机上也能正常使用（已使用响应式 Tailwind class，待真机测试）。

---

### Epic 9: 视频链接解析 ✅

**目标**: 粘贴链接 → 自动获取视频内容。

#### Task 9.1 — 集成 yt-dlp ✅
**优先级**: P0  
**文件**: `backend/services/link_parser.py`

**验收标准**:
- [x] 平台自动识别（抖音/小红书/B站/快手/YouTube/视频号/TikTok）
- [x] YouTube 链接测试通过（返回标题、作者、描述、缩略图）
- [x] 解析失败时返回友好错误信息
- [x] SSL 证书问题已解决（--no-check-certificates）

#### Task 9.2 — 链接解析 API ✅
**优先级**: P0  

**验收标准**:
- [x] `POST /api/parse-link` 端点实现
- [x] 返回统一的 ParseLinkResponse 结构
- [x] 降级逻辑：yt-dlp → 手动表单

#### Task 9.3 — 前端联动 ✅
**优先级**: P0  

**验收标准**:
- [x] AdForm 链接输入框启用
- [x] Enter/点击解析链接 → 自动填充表单
- [x] 缩略图预览、标题、作者、描述展示
- [x] 解析失败提示 + 手动表单 fallback

---

### Epic 10: 多媒体理解

**目标**: 从视频中提取文字、语音、画面。

#### Task 10.1 — 视频抽帧
**优先级**: P0  
**预估**: 1 天  
**描述**: 用 ffmpeg 场景检测 + 感知哈希去重。

**文件**: `backend/services/frame_extractor.py`

**验收标准**:
- [ ] 输入视频文件 → 输出关键帧（30-80 张）
- [ ] 场景变化检测（不是固定间隔）
- [ ] 去重（相似帧只保留一张）
- [ ] 帧以 base64 存储或临时文件

#### Task 10.2 — 语音转录
**优先级**: P0  
**预估**: 1 天  
**描述**: 用 faster-whisper 转录视频音频。

**文件**: `backend/services/transcriber.py`

**验收标准**:
- [ ] 输入视频/音频 → 输出带时间轴的转录文本
- [ ] 中文转录准确率 > 90%
- [ ] medium 模型在 Mac 上可用
- [ ] 首次运行时自动下载模型

#### Task 10.3 — OCR 文字提取
**优先级**: P1  
**预估**: 0.5 天  
**描述**: 从视频帧中提取叠加文字。

**文件**: `backend/services/ocr.py`

**验收标准**:
- [ ] 输入图片 → 输出画面中的中英文文字
- [ ] 按帧时间戳组织 OCR 结果

---

### Epic 11: 实时资讯管道

**目标**: 为宏观分析提供当下资讯背景。

#### Task 11.1 — 集成 newsbox
**优先级**: P1  
**预估**: 1 天  
**描述**: 配置 newsbox 定时抓取，缓存到 SQLite。

**文件**: `backend/services/live_intel.py`

**验收标准**:
- [ ] newsbox 后台定时运行（每 6 小时）
- [ ] 缓存到 `live_intel_cache` 表
- [ ] 分析广告时按关键词匹配返回 Top 10
- [ ] 过期数据自动清理

#### Task 11.2 — 宏观 Agent 增强
**优先级**: P1  
**预估**: 0.5 天  
**描述**: Agent 4 的 system prompt 中加入实时资讯。

**验收标准**:
- [ ] Agent 4 收到 `live_intel` 输入
- [ ] 笔记中引用实时资讯时标注来源和时间
- [ ] 如果无资讯，回退到 v0.1 模式

---

### Epic 12: 评分系统 & 知识库

**目标**: 量化评分 + 向量搜索 + Swipe File。

#### Task 12.1 — Agent 6: 评分 Agent ✅
**优先级**: P0  
**描述**: 20 维度评分 + 创意 DNA 提取（Mock 模式）。

**文件**: `backend/app/mock_pipeline.py` (`_build_scoring`)

**验收标准**:
- [x] 20 维度 1-5 评分，7 大类（hook/messaging/trust/conversion/emotion/production/innovation）
- [x] 综合分按权重计算（0-100）+ S/A/B/C/D 等级
- [x] 创意 DNA 输出（叙事模板、情绪公式、钩子结构、可复用元素）
- [x] Swipe 标签自动生成（#行业 #平台 #钩子 #价格 #信任 #评分 #品牌）

#### Task 12.2 — ScoreCard 前端组件 ✅
**优先级**: P0  

**验收标准**:
- [x] 环形分数显示 + 分类进度条
- [x] 创意 DNA 展示
- [x] Swipe 标签云
- [x] 集成到 ad detail 页面

#### Task 12.3 — Swipe File 页面 ✅
**优先级**: P1  

**验收标准**:
- [x] `/swipe` 页面卡片网格展示已完成分析广告
- [x] 按行业(9) × 平台(5) × 搜索词筛选
- [x] 卡片显示品牌/产品/洞察/状态/时间
- [x] 点击卡片跳转详情

#### Task 12.4 — Embedding + FAISS
**优先级**: P1  
**状态**: 待 v0.3  

#### Task 12.5 — Swipe File 高级 API
**优先级**: P1  
**状态**: 待 v0.3

---

### Epic 13: v0.2 集成 & 测试

#### Task 13.1 — 端到端烟雾测试
**优先级**: P0  
**预估**: 1 天  
**描述**: 用真实抖音/TikTok 链接完整跑通 v0.2 管道。

**验收标准**:
- [ ] 链接解析 → 内容抓取 → 多媒体理解 → Agent 分析 → 评分 → 入库
- [ ] 每一步有日志
- [ ] 失败时正确降级

#### Task 13.2 — Mock 模式保留
**优先级**: P1  
**预估**: 0.5 天  
**描述**: v0.2 也必须支持 Mock 模式（不依赖外部服务和 API）。

**验收标准**:
- [ ] 设置 `MOCK_MODE=true` 时，跳过链接解析和多媒体处理
- [ ] 使用 v0.1 的 mock_pipeline 增强版（含评分）

---

## v0.2 开发顺序

```
Epic 8 (UI) ✅ ──→ Epic 9 (链接解析) ✅ ──→ Epic 12 (评分+Swipe) ✅
                                                      │
                              Epic 10 (多媒体) ← 待 v0.3
                              Epic 11 (资讯)   ← 待 v0.3
                                                      │
                              Epic 13 (集成测试) ← 当前
```

**关键里程碑**:
1. ✅ Epic 8 完成 → UI 好看可用
2. ✅ Epic 9 完成 → 粘贴链接就能解析
3. ✅ Epic 12 完成 → 评分 + Swipe File 可用
4. ⏳ Epic 10 → 需要装 ffmpeg/Whisper（~3GB）
5. ⏳ Epic 3 → 需要 DMXAPI Key

---

## DMXAPI 接入任务（单独）

### Task X.1 — 注册 DMXAPI 账户（手动）
- [ ] 访问 https://doc.dmxapi.cn/kaishi.html
- [ ] 注册账户，获取 API Key
- [ ] 确认 DMXAPI 支持的视觉模型列表

### Task X.2 — 模型选型测试（手动）
- [ ] 测试视觉模型能否分析视频帧
- [ ] 测试文本模型的 JSON 输出稳定性
- [ ] 确定每个 Agent 的最佳模型

### Task X.3 — 配置本地环境
- [ ] 复制 `.env.example` 为 `.env`
- [ ] 填入 DMXAPI 配置
