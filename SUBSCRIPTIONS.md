# 信息源订阅

## GitHub — 同类项目关注

| 项目 | 关注点 | 方式 |
|------|--------|------|
| [LazyReel](https://github.com/dylanpakd-cyber/lazyreel) | 创意研究方法论、hook 分类、breakout 验证 | Star + Watch Releases |
| [claude-ads](https://github.com/AgriciDaniel/claude-ads) | Agent 架构、行业模板、评分算法 | Star + Watch Releases |
| [Agentic Video Editor](https://github.com/poseljacob/agentic-video-editor) | Reviewer 反馈循环、多模态编辑 | Star |
| [eonik Creative Audit](https://github.com/eonik-ai/eonik-creative-audit-skill) | Meta 广告创意衰减检测 | Star |

### GitHub 关键词搜索（定期查看 Trending）

```
topic:ad-analysis topic:ai-agent topic:video-analysis
"ad creative" agent pipeline
"multi-agent" advertising
"video understanding" ad
multimodal ad analysis
```

## 学术论文

| 来源 | 关键词 | 频率 |
|------|--------|------|
| [arxiv.org (cs.CL + cs.CV)](https://arxiv.org) | "advertisement understanding", "video ad", "multimodal ad", "creative analysis", "marketing AI" | 每周 |
| [HuggingFace Daily Papers](https://huggingface.co/papers) | 筛选 multimodal、video understanding 方向 | 每日 |
| [Papers With Code](https://paperswithcode.com) | "video advertisement", "ad creative", "multimodal summarization" | 每月 |

### 重点关注论文方向

- **Multimodal ad understanding**: SUMMA (arxiv 2508.20582), 视频广告结构化理解
- **Agentic video editing**: EditDuet (SIGGRAPH 2025), DIRECT (CVPR 2026)
- **LLM-as-judge**: 自动评估生成质量，可用于校准 scoring agent

## 行业动态

| 来源 | 关注点 |
|------|--------|
| [LatePost 晚点](https://www.latepost.com) | 中国广告/电商/AI 行业深度 |
| [36氪 AI 频道](https://36kr.com/information/AI) | AI 应用落地案例 |
| [广告黑榜](https://www.zhihu.com/column/ad-blacklist) | 广告创意案例分析（知乎专栏） |
| [SocialBeta](https://socialbeta.com) | 品牌营销案例拆解 |
| [即刻 App 广告圈](https://web.okjike.com) | 一线广告人/优化师的真实讨论 |

## 模型动态

| 模型 | 关注点 |
|------|--------|
| **doubao-seed-2-0** | 视频理解能力演进，新版本 API 变化 |
| **faster-whisper** | 新模型 size、语言支持改进 |
| **GPT-5.x / Claude 4.x** | 多模态推理能力提升，可能替代部分 agent |
| **Qwen-VL / InternVL** | 国产多模态模型进展，可作为成本更低的备选 |

## 维护方式

- GitHub Stars 每周检查一次，看是否有重大更新
- arXiv 搜索用 RSS 订阅，关键词: `(advertisement OR "ad creative") AND (multimodal OR "video understanding" OR agent)`
- 行业信息随手扔 `findings.md`，正式的技术参考记入 `devlog/`
- 每完成一个 P 阶段，更新 `SUBSCRIPTIONS.md` 中关注的模型和项目
