# 2026-06-07 — P3 验证与壁垒

## 3.3 多平台原生解析

### 目标
为 小红书、快手、视频号 添加原生 HTTP 解析器，替代 yt-dlp fallback。

### 变更清单
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `backend/services/link_parser.py` | 修改 | 新增 `_fetch_page()` 共享 helper + `_parse_xiaohongshu()` + `_parse_kuaishou()` + `_parse_shipinhao()`；更新 `parse_link()` dispatch |
| `backend/tests/test_link_parser.py` | 修改 | 新增 8 个测试覆盖三平台解析 + 超时处理 |

### 决策记录
- **小红书**：brace counting 提取 `__INITIAL_STATE__` JSON（参考 xhs-downloader 模式），回退到 og meta tags
- **快手**：复用 `_extract_json_blocks()`，尝试 photoId → videoId → photo_id → video_id
- **视频号**：best-effort（meta tags + JSON blocks），失败则 fall through 到 yt-dlp（微信鉴权限制）
- **共享 helper**：`_fetch_page(url)` 提取 Douyin 中的 mobile UA + follow_redirects 模式

## 3.2 创意 A/B 预测

### 目标
两条广告侧面对比分析，LLM 预测优势方。

### 变更清单
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `backend/app/comparison_engine.py` | 新增 | LLM 对比 pipeline：`run_comparison()` + `_build_comparison_context()` |
| `backend/app/routers/ads.py` | 修改 | 新增 `POST /api/compare` 端点 |
| `backend/app/schemas.py` | 修改 | 新增 `CompareRequest`、`CompareResponse`、`ComparisonDetail` |
| `frontend/lib/api.ts` | 修改 | 新增 `compareAds()` + 类型 |
| `frontend/app/compare/page.tsx` | 新增 | 对比页面：双栏搜索选择 + 结果展示 |
| `backend/tests/test_comparison.py` | 新增 | 5 个测试 |

### 决策记录
- **对比维度**：钩子 → 信息传递 → 转化 → 情绪 → 信任 → 制作 → 创新（7 维，与评分体系一致）
- **输出**：predicted_winner (A/B/tie) + confidence (high/medium/low) + 各维度对比文字
- **前端交互**：搜索选择式（复用 `searchAds` 语义搜索），结果页面展示胜负 + 关键差异 + 分析正文

## 3.1 创意评分人类校准

### 目标
收集专家评分，计算 Spearman ρ 相关系数，量化 AI 评分与人类判断的一致性。

### 变更清单
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `backend/app/database.py` | 修改 | 新增 `expert_scores` 表 + `_create_expert_scores()` |
| `backend/app/routers/calibration.py` | 新增 | Spearman ρ 纯 Python 实现 + 3 个端点（提交/列表/报告） |
| `backend/app/main.py` | 修改 | 注册 calibration router |
| `frontend/lib/api.ts` | 修改 | 新增 `submitExpertScore()`、`listExpertScores()`、`fetchCalibrationReport()` |
| `frontend/app/calibration/page.tsx` | 新增 | 评分页面：广告列表 + 滑块打分 + AI 参考值 |
| `frontend/app/calibration/report/page.tsx` | 新增 | 报告页面：ρ 汇总 + 维度表 + 信度 + 柱状图 |

### 决策记录
- **纯 Python 统计**：无 scipy 依赖，`_rankdata()` + `_spearman_rho()` + Student's t CDF 近似
- **维度映射**：AI 7 个 category 各含 2-3 子维度 → 取均值得 1-5 分，与专家 1-5 分对比
- **等级一致率**：AI 的 S/A/B/C/D tier vs 专家 overall_score 映射的 tier
- **专家信度**：每位专家 vs 其余专家均值的 pairwise Spearman ρ

## 验证
- [x] 所有 45 个测试通过
- [x] 前端 TypeScript 编译通过
- [ ] 小红书/快手/视频号真实链接端到端解析
- [ ] 真实 LLM A/B 对比端到端验证
- [ ] 真实专家评分数据输入后校准报告验证

## 下一步
Roadmap 全部完成。可考虑：性能优化（A2+A3 并行、上下文裁剪）、部署上线、真实用户测试。
