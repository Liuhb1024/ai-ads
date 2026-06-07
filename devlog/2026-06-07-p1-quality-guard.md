# 2026-06-07 — P1 质量护栏（完整）

## 目标
完成 P1 三大质量护栏任务，参考 LazyReel 和 claude-ads 的实际实现方法论。

## 变更清单
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `backend/app/agent_pipeline.py` | 修改 | Agent 2 新增 `hook_pattern` 字段（13 种结构化分类），system prompt 加入强制分类指令 |
| `backend/app/reporting.py` | 修改 | 报告新增 `_hook_pattern_display()` 展示钩子模式 |
| `backend/app/mock_pipeline.py` | 修改 | mock 模式同步输出 `hook_pattern` 字段 |
| `backend/app/publishing_pipeline.py` | 修改 | 新增 anti-slop 检测系统（10 组正则模式），集成到候选选择流程 |
| `backend/app/analysis_quality.py` | 修改 | 新增 `_compute_severity()` 严重性乘数系统（Critical ×5.0/Major ×3.0/Moderate ×2.0） |
| `tools/headroom-dashboard.html` | 新增 | headroom 压缩统计可视化面板 |

## 决策记录

### 1.1 结构化 Hook 分类
- **参考来源**：LazyReel 的 13 hook pattern taxonomy（POV, belief-challenging, direct call-out 等）
- **设计决策**：`hook_pattern` 与 `hook_type` 并存而非替换——前者用于结构化分类和跨广告对比，后者保留 LLM 自由描述钩子细节
- **中文适配**：将"founder story"改为"创始人叙事"，增加"场景还原"（中文广告高频模式）

### 1.2 Anti-Slop 输出检查
- **参考来源**：LazyReel 的 `kill_the_slop` 工具 + 中文广告文案实际分析
- **设计决策**：10 组中文正则模式，硬阈值 2 个匹配。命中超阈值时自动切换到备选候选，两版都超标则回退到 `_fallback_output`
- **写入 `_editorial_meta`**：slop 检测结果和 swap 原因均记录在元数据中

### 1.3 严重性乘数
- **参考来源**：claude-ads 的 severity multiplier 系统（Critical ×5.0，3× Kill Rule）
- **设计决策**：Agent 5 和 Agent 6 有硬依赖（Agent 6 需要 safe_claims），无法并行化。替代方案是在本地质量门加入严重性乘数：
  - Critical（×5.0）：>50% claims 被拒 或 >3 矛盾 → hard_penalty=40，触发 kill
  - Major（×3.0）：>30% 被拒 或 >2 矛盾 → hard_penalty=20
  - Moderate（×2.0）：>15% 被拒 或 证据薄弱度 >0.3
- **kill_trigger**：Critical 等级强制 `trust_score ≤ 39`、`verdict = "reject"`

## 验证
- [x] 所有 Python 文件可通过 import
- [x] `check_slop()` 检测正确（正常文本 0 匹配，重度 slop 5 匹配）
- [x] `_fallback_output` 文本不含 slop（0 匹配）
- [x] `_compute_severity()` 三级严重性分级正确
- [x] mock_pipeline 产出包含 `hook_pattern` 字段
- [ ] 真实 LLM pipeline 端到端验证（需跑一条广告确认）

## 遇到的问题

### WebFetch 无法访问 GitHub
- 项目 README 和源码无法通过 WebFetch 直接获取
- 通过 WebSearch + 搜索结果交叉验证确认了设计方向

### Agent 5/6 并行化不可行
- 原计划并行化 Agent 5（审计）和 Agent 6（评分）
- 实际代码分析发现 Agent 6 硬依赖 Agent 5 的 `safe_claims` 和 `audit`
- 改为实现 claude-ads 的严重性乘数系统作为替代优化

## 下一步
P2: Swipe File 语义搜索 + 行业差异化分析模板 + 发布稿迭代优化
