import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.workflow import continue_job, critical_missing_fields, normalize_scoring


class WorkflowRulesTests(unittest.TestCase):
    def test_requires_confirmation_for_missing_product(self):
        self.assertEqual(
            critical_missing_fields(
                {"brand_name": "元气森林", "product_name": "", "industry": "食品"}
            ),
            ["product_name"],
        )

    def test_complete_metadata_can_continue(self):
        self.assertEqual(
            critical_missing_fields(
                {"brand_name": "元气森林", "product_name": "好自在饮料", "industry": "食品"}
            ),
            [],
        )

    def test_unwraps_real_agent_scoring_shape(self):
        value = {
            "scoring": {
                "scoring": {"overall_score": 77, "tier": "A级"},
                "creative_dna": {"narrative_template": "问题-方案"},
                "swipe_tags": ["#行业_食品"],
            }
        }
        normalized = normalize_scoring(value)
        self.assertEqual(normalized["scoring"]["overall_score"], 77)
        self.assertEqual(normalized["creative_dna"]["narrative_template"], "问题-方案")


class WorkflowVideoRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_continue_job_passes_downloaded_video_to_agent_pipeline(self):
        row = {
            "parsed_title": "测试广告",
            "ad_title": "测试广告",
            "brand_name": "测试品牌",
            "product_name": "测试产品",
            "industry": "食品",
            "price_range": None,
            "ad_copy": "原始文案",
            "scene_description": None,
            "screenshot_description": None,
            "user_context": None,
            "seen_at": None,
            "source_platform": "抖音",
            "platform": "抖音",
            "source_url": "https://v.douyin.com/example/",
            "media_path": "/tmp/downloaded-video.mp4",
            "transcript_json": '{"full_text":"转写内容"}',
        }
        media = SimpleNamespace(
            video_path="/tmp/downloaded-video.mp4",
            frame_base64=[{"base64": "frame", "mime_type": "image/jpeg"}],
        )
        analysis = {"scoring": {}, "final_note": {}}

        with (
            patch("app.workflow._get_job", AsyncMock(return_value=row)),
            patch("app.workflow._set_stage", AsyncMock()),
            patch("app.workflow._update", AsyncMock()),
            patch("app.workflow.run_agent_pipeline", AsyncMock(return_value=analysis)) as pipeline,
            patch(
                "app.workflow.generate_publishing_output",
                AsyncMock(return_value={"douyin_article": {}, "douyin_script": {}, "xiaohongshu": {}}),
            ),
        ):
            await continue_job("job123", media=media)

        kwargs = pipeline.await_args.kwargs
        self.assertEqual(kwargs["video_path"], "/tmp/downloaded-video.mp4")
        self.assertEqual(kwargs["video_url"], "https://v.douyin.com/example/")
        self.assertEqual(kwargs["frames_base64"][0]["base64"], "frame")


if __name__ == "__main__":
    unittest.main()
