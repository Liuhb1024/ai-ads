# Full Report Sections Design

## Problem

The current deterministic report is stable and exportable, but too compressed. It shows evidence, score, claims, risks, and publishing outputs, while hiding rich agent fields such as material breakdown, strategy structure, user psychology, macro context, and personal takeaways.

## Design

The report should become a full editorial research note with explicit sections:

1. 素材解构：商品、画面、人物、动作、转场、文案、视觉、广告结构。
2. 广告策略分析：投放目标、漏斗位置、钩子、信任建立、转化收尾、竞争定位。
3. 用户洞察：目标画像、显性/隐性/情绪痛点、三层欲望、受众假设。
4. 宏观背景：消费趋势、平台生态、社会情绪、时机判断、时效限制。
5. 对我的启发：自媒体、抖音、小红书、电商、AI 漫剧/IP 内容的可复用动作。

The report remains deterministic. It maps existing structured agent outputs into richer Markdown instead of asking another model to write arbitrary prose. Unsupported claims stay hidden from main sections and remain listed in risk review.

## Compatibility

Old completed jobs should display the new report when opened. The API will rebuild `final_note.markdown_content` from saved structured analysis and publishing data in `GET /api/jobs/{id}`. Export endpoints already rebuild from the same source.

## Validation

Tests assert that the report contains all expected sections and key agent details. Browser and PDF export verification must confirm the new long-form report renders correctly.

