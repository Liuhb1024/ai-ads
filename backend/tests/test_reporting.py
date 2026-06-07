import unittest

from app.reporting import build_report_markdown


class ReportBuilderTests(unittest.TestCase):
    def test_builds_professional_report_with_evidence_and_publication(self):
        report = build_report_markdown(
            {
                "id": "abc123",
                "brand_name": "元气森林",
                "product_name": "好自在",
                "industry": "食品",
                "platform": "抖音",
                "created_at": "2026-06-07 12:00:00",
            },
            {
                "analysis_meta": {
                    "video_model": "doubao-seed-2-0-lite-260215",
                    "source_mode": "video",
                    "evidence_count": 1,
                    "trust_score": 88,
                    "audit_verdict": "pass",
                },
                "material_understanding": {
                    "product_summary": {
                        "brand": "元气森林",
                        "product": "好自在",
                        "category": "植物饮料",
                        "price_segment": "中价促销",
                        "usp": "多口味大包装，强调囤货划算",
                    },
                    "scene_breakdown": {
                        "setting": "室内产品陈列与试饮场景",
                        "characters": ["年轻男性试饮"],
                        "actions": ["倒饮展示色泽", "展示整箱30瓶", "试喝并描述口感"],
                        "tone": "促销种草",
                        "transitions": "产品特写与陈列镜头快切",
                    },
                    "copy_analysis": {
                        "headline": "好自在这波真赢麻了",
                        "key_claims": ["线下高价对比", "整整30瓶", "到手价129.8"],
                        "cta": "抖音搜索官方旗舰店",
                        "copy_style": "口播带货",
                        "has_music": True,
                        "has_voiceover": True,
                        "has_text_overlay": True,
                    },
                    "visual_elements": {
                        "dominant_colors": ["原木色", "白色"],
                        "text_overlays": ["真赢麻了", "年货节狂欢购"],
                        "shot_type": "产品特写+陈列混剪",
                        "visual_effects": ["字幕叠加"],
                    },
                    "evidence_ledger": [
                        {
                            "id": "E001",
                            "timestamp": "00:02",
                            "modality": "visual",
                            "observation": "画面出现30瓶饮料",
                            "quote": "",
                            "confidence": "high",
                        }
                    ]
                },
                "ad_strategy": {
                    "target_audience_clue": {
                        "demographic_hints": ["价格敏感型饮料消费者"],
                        "interest_hints": ["囤货", "低糖饮料"],
                        "platform_behavior_hints": ["抖音搜索下单"],
                    },
                    "ad_objective": {
                        "primary_goal": "转化下单",
                        "secondary_goal": "口味种草",
                        "funnel_stage": "决策/转化阶段",
                    },
                    "creative_strategy": {
                        "hook_type": "价格反差型",
                        "trust_building": "整箱陈列与试饮",
                        "closing_tactic": "官方店搜索",
                        "narrative_structure": "反差钩子-多口味证明-价格收口",
                    },
                    "competitive_positioning": {
                        "differentiation": "多口味与囤货价格",
                        "benchmark_against": "线下购买场景",
                        "market_timing_rationale": "年货节促销",
                    },
                    "claims": [
                        {
                            "claim": "用数量与价格反差建立吸引力",
                            "claim_type": "inferred",
                            "confidence": "high",
                            "evidence_ids": ["E001"],
                            "support_status": "partially_supported",
                            "counterpoint": "也可能只是促销信息展示",
                        }
                    ]
                },
                "user_insight": {
                    "target_user_profile": {
                        "age_range": "20-35",
                        "gender_tendency": "不限",
                        "city_tier": "一二线及新一线",
                        "occupation_clues": ["上班族"],
                        "lifestyle_tags": ["轻养生", "囤货"],
                        "consumption_level": "中等",
                    },
                    "pain_points": {
                        "explicit_pain": ["饮料选择多但怕踩雷"],
                        "implicit_pain": ["担心囤多喝不完"],
                        "emotional_pain": ["不想买贵了"],
                    },
                    "desire_mapping": {
                        "surface_desire": "买到便宜好喝的饮料",
                        "deep_desire": "减少选择成本",
                        "identity_desire": "成为会买、会囤的精明消费者",
                    },
                    "claims": [],
                },
                "macro_context": {
                    "consumption_trends": [
                        {
                            "trend_name": "质价比消费",
                            "relevance": "通过大包装和到手价建立划算感",
                            "confidence": "inferred",
                        }
                    ],
                    "platform_dynamics": {
                        "platform": "抖音",
                        "current_hotspot_relevance": "仅能判断素材借用了促销节奏",
                        "content_trend_match": "短视频带货常见结构",
                        "algorithm_friendliness": "快节奏信息密度较高",
                    },
                    "social_sentiment": {
                        "dominant_emotion": "怕买贵、想占便宜",
                        "cultural_context": "促销节点中的精明消费",
                        "value_appeal": "低门槛囤货与安心选择",
                    },
                    "timing_analysis": "素材使用年货节福利表达，但无法验证投放日期。",
                    "claims": [],
                },
                "quality_audit": {
                    "trust_score": 88,
                    "verdict": "pass",
                    "unsupported_claims": [],
                    "contradictions": [],
                    "limitations": ["无后台转化数据"],
                },
                "scoring": {
                    "scoring": {
                        "overall_score": 76,
                        "tier": "A级",
                        "score_breakdown_note": "钩子明确，效果数据未知。",
                    },
                    "creative_dna": {"narrative_template": "价格反差-数量证明-行动引导"},
                },
                "final_note": {"one_sentence_takeaway": "这条广告卖的是低门槛囤货的确定感。"},
            },
            {
                "douyin_article": {
                    "title": "30瓶饮料，卖的不是便宜",
                    "hook": "先说结论。",
                    "body": "正文内容",
                    "cta": "你怎么看？",
                    "hashtags": ["#广告拆解"],
                },
                "douyin_script": {
                    "duration_seconds": 75,
                    "full_script": "完整口播稿",
                },
                "xiaohongshu": {
                    "titles": ["标题一", "标题二", "标题三"],
                    "body": "小红书正文",
                    "hashtags": ["#营销观察"],
                    "image_card_ideas": ["首图"],
                },
            },
        )

        self.assertIn("# 元气森林「好自在」广告创意研究报告", report)
        self.assertIn("doubao-seed-2-0-lite-260215", report)
        self.assertIn("| E001 | 00:02 |", report)
        self.assertIn("可信度评分：**88/100**", report)
        self.assertIn("## 04｜素材解构", report)
        self.assertIn("### 广告结构", report)
        self.assertIn("## 05｜广告策略分析", report)
        self.assertIn("转化下单", report)
        self.assertIn("## 06｜用户洞察", report)
        self.assertIn("显性痛点", report)
        self.assertIn("## 07｜宏观背景", report)
        self.assertIn("质价比消费", report)
        self.assertIn("## 08｜对我的启发", report)
        self.assertIn("如果我做抖音/自媒体", report)
        self.assertIn("## 11｜抖音发布包", report)
        self.assertIn("完整口播稿", report)


if __name__ == "__main__":
    unittest.main()
