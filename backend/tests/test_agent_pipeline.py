import unittest
from unittest.mock import AsyncMock, patch

from app.agent_pipeline import run_agent_pipeline
from app.llm_client import VIDEO_MODEL


class AgentPipelineVideoTests(unittest.IsolatedAsyncioTestCase):
    async def test_uses_configured_doubao_model_for_video(self):
        video_result = {
            "evidence_ledger": [],
            "product_summary": {},
            "scene_breakdown": {},
            "copy_analysis": {},
            "visual_elements": {},
            "confidence": {"overall": "high"},
        }
        generic_result = {
            "content": "# report",
            "fact_check_summary": {
                "observed_facts": [],
                "user_provided_context": [],
                "model_inference": [],
                "uncertainty": [],
            },
        }

        with (
            patch("app.agent_pipeline.chat_completion_video", AsyncMock(return_value=video_result)) as video,
            patch("app.agent_pipeline.chat_completion", AsyncMock(return_value=generic_result)),
        ):
            await run_agent_pipeline({"brand_name": "品牌"}, video_path="/tmp/video.mp4")

        self.assertEqual(video.await_args.kwargs["model"], VIDEO_MODEL)
        self.assertEqual(VIDEO_MODEL, "doubao-seed-2-0-lite-260215")

    async def test_video_failure_falls_back_to_frame_vision_before_text(self):
        vision_result = {
            "evidence_ledger": [{"id": "E1", "timestamp": "00:00", "observation": "出现产品"}],
            "product_summary": {},
            "scene_breakdown": {},
            "copy_analysis": {},
            "visual_elements": {},
            "confidence": {"overall": "medium"},
        }

        with (
            patch(
                "app.agent_pipeline.chat_completion_video",
                AsyncMock(return_value={"_error": "video request failed"}),
            ),
            patch(
                "app.agent_pipeline.chat_completion_vision",
                AsyncMock(return_value=vision_result),
            ) as vision,
            patch(
                "app.agent_pipeline.chat_completion",
                AsyncMock(return_value={"content": "# report"}),
            ),
        ):
            result = await run_agent_pipeline(
                {"brand_name": "品牌"},
                video_path="/tmp/video.mp4",
                frames_base64=[{"base64": "frame", "mime": "image/jpeg"}],
            )

        vision.assert_awaited_once()
        self.assertEqual(result["analysis_meta"]["source_mode"], "frames_fallback")
        self.assertEqual(result["analysis_meta"]["video_model"], VIDEO_MODEL)


if __name__ == "__main__":
    unittest.main()
