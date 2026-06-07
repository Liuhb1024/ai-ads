# 2026-06-07 — 行业差异化分析模板 (P2.2)

## 目标
Agent 2（策略）和 Agent 3（用户洞察）当前对所有行业使用完全相同的分析框架，导致美妆/3C/教育等不同行业的分析千篇一律。参考 claude-ads 行业模板设计差异化分析维度。

## 变更清单
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `backend/app/agent_pipeline.py` | 修改 | 新增 `_INDUSTRY_DIMENSIONS` 7 行业维度字典 + `_industry_guide()` 匹配函数，注入到 Agent 2/3 的 user prompt |
| `devlog/performance-optimization-notes.md` | 新增 | 性能优化策略记录（A2+A3 并行、上下文裁剪、小模型轻任务） |

## 决策记录
- **参考来源**：claude-ads 的 11 套行业模板（SaaS、电商、本地服务等），适配为中文广告场景的 7 行业
- **注入位置**：Agent 2（广告策略）和 Agent 3（用户洞察），因为这两个 agent 做判断推理，最受益于行业知识校准
- **匹配策略**：子串匹配（"护肤美妆" → "美妆"），未匹配或 `industry == "其他"` 时用通用模板
- **行业覆盖**：美妆、食品、3C、教育、电商、金融、游戏 + 通用兜底
- **不在 mock 中区分**：mock pipeline 已有 `_infer_demographic()` 等确定性规则，本身按行业区分，无需适配

## 验证
- [x] 所有 30 个测试通过
- [x] `_industry_guide()` 模糊匹配正确（"护肤美妆"→"美妆"）
- [x] 空字符串/其他 → 通用模板 fallback
- [ ] 真实 LLM pipeline 端到端验证（美妆/3C 广告报告应有差异化分析视角）

## 遇到的问题
无

## 下一步
2.1 Swipe File 语义搜索（sentence-transformers + faiss）或 2.3 发布稿迭代优化
