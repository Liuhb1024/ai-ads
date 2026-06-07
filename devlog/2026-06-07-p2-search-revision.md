# 2026-06-07 — 发布稿迭代优化 (P2.3) + Swipe File 语义搜索 (P2.1)

## P2.3 发布稿迭代优化

### 目标
当 judge 评出的入选稿 clarity 或 actionability < 7 时，自动用评审反馈做一轮修订。

### 变更清单
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `backend/app/publishing_pipeline.py` | 修改 | 新增 `_revise_candidate()`、`_winner_judge_scores()`、`REVISION_SYSTEM`；在 `generate_publishing_output()` 中反 slop 检查后判断是否需要修订 |
| `backend/tests/test_publishing_pipeline.py` | 修改 | 增加 `test_revises_winner_when_clarity_actionability_below_seven` 测试，原有测试用 ≥7 分避免触发修订 |

### 决策记录
- **触发阈值**：clarity < 7 或 actionability < 7（任一不达标即修订）
- **轮数限制**：最多 1 轮修订（避免无限循环拉高延迟）
- **评分聚合**：取 forward/reverse 两轮 judges 的 `min` 值，保守估计
- **修订范围**：只针对薄弱维度（clarity → 观点聚焦、表述直白；actionability → 补充可复用启示）
- **失败策略**：修订 LLM 调用失败则返回原稿，不阻塞流程

### 验证
- [x] 所有 31 个测试通过
- [x] 高评分稿不触发修订（await_count=3）
- [x] 低评分稿触发修订并成功替换（await_count=4）

## P2.1 Swipe File 语义搜索

### 目标
Swipe File 页面从客户端子串匹配升级为语义搜索（sentence-transformers embedding + FAISS 索引）。

### 变更清单
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `backend/app/swipe_index.py` | 新增 | 语义搜索模块：lazy load SentenceTransformer（paraphrase-multilingual-MiniLM-L12-v2）+ FAISS IndexFlatIP，`build_index()` 从 DB 构建索引，`search()` 执行相似度查询 |
| `backend/app/routers/ads.py` | 修改 | 新增 `GET /api/ads/search?q=...&top_k=...` 端点 |
| `backend/requirements.txt` | 修改 | 新增 `sentence-transformers>=3.0.0`、`faiss-cpu>=1.8.0` |
| `frontend/lib/api.ts` | 修改 | 新增 `searchAds()` 函数和 `SearchResult` 类型 |
| `frontend/app/swipe/page.tsx` | 修改 | 搜索输入框改为语义搜索（300ms 防抖），回退到列表 |

### 决策记录
- **模型选择**：`paraphrase-multilingual-MiniLM-L12-v2`（384 维，支持中文，轻量 ~120MB）
- **索引策略**：内存索引（IndexFlatIP + L2 normalize = cosine similarity），启动时首次使用按需构建
- **前端降级**：语义搜索 API 调用失败时自动回退到客户端子串过滤
- **防抖**：300ms，减少 API 调用
- **不去重**：维持简单实现，未来可增量更新索引

### 验证
- [x] 后端 31 个测试通过
- [x] `swipe_index` 模块导入成功（sentence-transformers/faiss lazy load）
- [x] 前端 TypeScript 编译通过
- [ ] 端到端语义搜索验证（需真实 embedding 模型）

## 遇到的問題
无

## 下一步
P2 阶段完成。P3 长期目标：创意评分人类校准、A/B 预测、多平台适配。
