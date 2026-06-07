import unittest
from unittest.mock import AsyncMock, patch

from app.publishing_pipeline import (
    _fallback_output,
    _select_candidate,
    _valid_output,
    generate_publishing_output,
)


class PublishingPipelineTests(unittest.TestCase):
    def test_fallback_contains_all_separate_publication_outputs(self):
        result = _fallback_output(
            {"brand_name": "元气森林", "product_name": "好自在饮料"},
            {"final_note": {"one_sentence_takeaway": "用价格反差制造确定性。"}},
        )
        self.assertTrue(_valid_output(result))
        self.assertIn("body", result["douyin_article"])
        self.assertIn("full_script", result["douyin_script"])
        self.assertGreaterEqual(result["douyin_script"]["duration_seconds"], 60)
        self.assertLessEqual(result["douyin_script"]["duration_seconds"], 90)
        self.assertGreaterEqual(len(result["xiaohongshu"]["titles"]), 3)

    def test_incomplete_model_output_is_rejected(self):
        self.assertFalse(_valid_output({"douyin_article": {}}))

    def test_position_balanced_judges_select_same_candidate(self):
        candidates = [
            {"candidate_id": "A", "douyin_article": {}, "douyin_script": {}, "xiaohongshu": {}},
            {"candidate_id": "B", "douyin_article": {}, "douyin_script": {}, "xiaohongshu": {}},
        ]
        winner = _select_candidate(
            candidates,
            {"winner": "B", "scores": {}},
            {"winner": "B", "scores": {}},
        )
        self.assertEqual(winner["candidate_id"], "B")


HIGH_SCORES = {"credibility": 8, "novelty": 8, "clarity": 8, "platform_fit": 8, "actionability": 8}


class PublishingGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_generates_two_candidates_and_judges_both_orders(self):
        base = {
            "douyin_article": {"title": "标题", "hook": "钩子", "body": "正文", "cta": "互动", "hashtags": []},
            "douyin_script": {"title": "口播", "duration_seconds": 75, "hook": "开头", "beats": [], "cta": "互动", "full_script": "全文"},
            "xiaohongshu": {"titles": ["1", "2", "3"], "body": "正文", "hashtags": [], "image_card_ideas": []},
        }
        candidate_a = {"candidate_id": "A", "concept_name": "证据拆解", **base}
        candidate_b = {"candidate_id": "B", "concept_name": "反常识切口", **base}
        forward = {"winner": "B", "scores": {"A": HIGH_SCORES, "B": HIGH_SCORES}, "reason": "B切入更独特"}
        reverse = {"winner": "B", "scores": {"A": HIGH_SCORES, "B": HIGH_SCORES}, "reason": "B更可执行"}

        with (
            patch("app.publishing_pipeline.is_configured", return_value=True),
            patch(
                "app.publishing_pipeline.chat_completion",
                AsyncMock(side_effect=[{"candidates": [candidate_a, candidate_b]}, forward, reverse]),
            ) as completion,
        ):
            result = await generate_publishing_output(
                {"brand_name": "品牌", "product_name": "产品"},
                {
                    "material_understanding": {"evidence_ledger": [{"id": "E001", "observation": "出现产品"}]},
                    "ad_strategy": {"claims": []},
                    "user_insight": {"claims": []},
                    "macro_context": {"claims": []},
                    "quality_audit": {"verdict": "pass", "trust_score": 90},
                },
            )

        self.assertEqual(completion.await_count, 3)
        self.assertEqual(result["_editorial_meta"]["selected_candidate"], "B")
        reverse_prompt = completion.await_args_list[2].kwargs["user"]
        self.assertLess(reverse_prompt.index('"candidate_id": "B"'), reverse_prompt.index('"candidate_id": "A"'))

    async def test_revises_winner_when_clarity_actionability_below_seven(self):
        base = {
            "douyin_article": {"title": "标题", "hook": "钩子", "body": "正文", "cta": "互动", "hashtags": []},
            "douyin_script": {"title": "口播", "duration_seconds": 75, "hook": "开头", "beats": [], "cta": "互动", "full_script": "全文"},
            "xiaohongshu": {"titles": ["1", "2", "3"], "body": "正文", "hashtags": [], "image_card_ideas": []},
        }
        candidate_a = {"candidate_id": "A", "concept_name": "证据拆解", **base}
        candidate_b = {"candidate_id": "B", "concept_name": "反常识切口", **base}
        low_scores = {"credibility": 6, "novelty": 5, "clarity": 4, "platform_fit": 6, "actionability": 3}
        forward = {"winner": "A", "scores": {"A": low_scores, "B": HIGH_SCORES}, "reason": "A观点更聚焦但表述模糊"}
        reverse = {"winner": "A", "scores": {"A": low_scores, "B": HIGH_SCORES}, "reason": "A切口独特但缺少操作建议"}

        revised = dict(candidate_a)
        revised["douyin_article"] = dict(candidate_a["douyin_article"])
        revised["douyin_article"]["body"] = "修订后更聚焦的正文"

        with (
            patch("app.publishing_pipeline.is_configured", return_value=True),
            patch(
                "app.publishing_pipeline.chat_completion",
                AsyncMock(side_effect=[{"candidates": [candidate_a, candidate_b]}, forward, reverse, revised]),
            ) as completion,
        ):
            result = await generate_publishing_output(
                {"brand_name": "品牌", "product_name": "产品"},
                {
                    "material_understanding": {"evidence_ledger": [{"id": "E001", "observation": "出现产品"}]},
                    "ad_strategy": {"claims": []},
                    "user_insight": {"claims": []},
                    "macro_context": {"claims": []},
                    "quality_audit": {"verdict": "pass", "trust_score": 90},
                },
            )

        self.assertEqual(completion.await_count, 4)
        self.assertTrue(result["_editorial_meta"]["revision"]["attempted"])
        self.assertTrue(result["_editorial_meta"]["revision"]["succeeded"])
        self.assertEqual(result["_editorial_meta"]["revision"]["pre_revision_clarity"], 4)
        self.assertEqual(result["_editorial_meta"]["revision"]["pre_revision_actionability"], 3)
        self.assertEqual(result["_editorial_meta"]["selected_candidate"], "A")


if __name__ == "__main__":
    unittest.main()
