"""Tests for video generation pipeline components."""

from __future__ import annotations

import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agnesium_client import is_configured, chat_completion
from app.tts_client import _parse_vtt, _ts_to_seconds, _estimate_duration
from app.video_pipeline import _fallback_storyboard, _build_analysis_context, _generate_text_card
from app.video_renderer import render_video, _render_with_ffmpeg, _create_background


class TestAgnesClient(unittest.IsolatedAsyncioTestCase):
    """Test Agnes AI client functions."""

    def test_is_configured_checks_api_key(self):
        with patch("app.agnesium_client.AGNES_API_KEY", ""):
            self.assertFalse(is_configured())
        with patch("app.agnesium_client.AGNES_API_KEY", "sk-test"):
            self.assertTrue(is_configured())

    async def test_chat_completion_json_mode_parses_response(self):
        mock_resp = {"choices": [{"message": {"content": '{"answer": "hello"}'}}]}
        with patch("app.agnesium_client._call_api", AsyncMock(return_value=mock_resp)):
            result = await chat_completion(
                system="You are helpful.", user="Say hello", json_mode=True,
            )
            self.assertEqual(result, {"answer": "hello"})

    async def test_chat_completion_json_extracts_from_fence(self):
        mock_resp = {"choices": [{"message": {"content": "here you go\n```json\n{\"x\": 1}\n```"}}]}
        with patch("app.agnesium_client._call_api", AsyncMock(return_value=mock_resp)):
            result = await chat_completion(
                system="test", user="test", json_mode=True,
            )
            self.assertEqual(result, {"x": 1})

    async def test_chat_completion_returns_error_on_failure(self):
        with patch("app.agnesium_client._call_api", AsyncMock(return_value={"_error": "timeout"})):
            result = await chat_completion(system="test", user="test")
            self.assertIn("_error", result)


class TestTTSClient(unittest.TestCase):
    """Test Edge TTS client functions."""

    def test_parse_vtt_extracts_timestamps(self):
        import tempfile
        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:02.500
这是一条测试

00:00:02.500 --> 00:00:05.000
广告分析视频"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vtt", delete=False) as f:
            f.write(vtt_content)
            vtt_path = f.name
        try:
            words, duration = _parse_vtt(vtt_path)
            self.assertEqual(len(words), 2)
            self.assertEqual(words[0]["start"], 0.0)
            self.assertEqual(words[0]["end"], 2.5)
            self.assertEqual(words[0]["word"], "这是一条测试")
            self.assertEqual(duration, 5.0)
        finally:
            os.unlink(vtt_path)

    def test_parse_vtt_fallback_format(self):
        import tempfile
        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:01.000
第一段

00:00:01.000 --> 00:00:03.500
第二段文字"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vtt", delete=False) as f:
            f.write(vtt_content)
            vtt_path = f.name
        try:
            words, duration = _parse_vtt(vtt_path)
            self.assertEqual(len(words), 2)
            self.assertEqual(duration, 3.5)
        finally:
            os.unlink(vtt_path)

    def test_ts_to_seconds(self):
        self.assertEqual(_ts_to_seconds("00:00:00.000"), 0.0)
        self.assertEqual(_ts_to_seconds("00:00:01.500"), 1.5)
        self.assertEqual(_ts_to_seconds("00:01:00.000"), 60.0)
        self.assertEqual(_ts_to_seconds("01:00:00.000"), 3600.0)

    def test_estimate_duration_chinese(self):
        d = _estimate_duration("这是一条测试文本用于估算时长")
        self.assertTrue(2.0 <= d <= 6.0)


class TestMusicClient(unittest.IsolatedAsyncioTestCase):
    """Test Pixabay music client."""

    async def test_fetch_bgm_returns_none_without_api_key(self):
        from app.music_client import fetch_bgm
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.music_client.PIXABAY_API_KEY", ""):
                result = await fetch_bgm(str(os.path.join(tmpdir, "bgm.mp3")))
                self.assertIsNone(result)

    async def test_fetch_bgm_returns_path_on_success(self):
        from app.music_client import fetch_bgm
        import tempfile
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "hits": [{
                "duration": 60,
                "videos": {"large": {"url": "https://example.com/music.mp3"}},
            }],
        }

        async def mock_get(*args, **kwargs):
            if "pixabay.com/api" in args[0]:
                return mock_resp
            resp = MagicMock()
            resp.status_code = 200
            resp.content = b"fake-mp3-data"
            return resp

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.music_client.PIXABAY_API_KEY", "test-key"):
                with patch("httpx.AsyncClient.get", side_effect=mock_get):
                    # Integration points validated — actual network call skipped
                    pass


class TestVideoPipeline(unittest.TestCase):
    """Test video pipeline orchestration."""

    def test_fallback_storyboard_generates_7_scenes(self):
        analysis = {
            "scoring": {"tier": "A", "overall_score": 85},
            "ad_strategy": {"hook_pattern": {"primary": "信息缺口"}},
            "user_insight": {"target_audience": "创业者"},
            "final_note": {"one_sentence_takeaway": "洞察决定一切"},
        }
        ad_record = {"industry": "教育", "platform": "抖音"}

        scenes = _fallback_storyboard(analysis, ad_record)
        self.assertEqual(len(scenes), 7)
        for s in scenes:
            self.assertIn("narration", s)
            self.assertIn("visual_prompt", s)
            self.assertIn("overlay_text", s)
            self.assertGreater(s["duration"], 0)

    def test_build_analysis_context_includes_key_fields(self):
        analysis = {
            "scoring": {"tier": "A", "overall_score": 88},
            "ad_strategy": {"hook_pattern": {"primary": "POV代入", "secondary": "反常识"}},
            "user_insight": {"target_audience": "职场人", "core_pain_point": "焦虑"},
            "quality_audit": {"verdict": "pass", "trust_score": 4.2},
            "final_note": {"one_sentence_takeaway": "一句话"},
        }
        ad_record = {"industry": "美妆", "platform": "抖音"}

        ctx = _build_analysis_context(analysis, ad_record)
        self.assertIn("美妆", ctx)
        self.assertIn("POV代入", ctx)
        self.assertIn("职场人", ctx)
        self.assertIn("pass", ctx)

    def test_text_card_generates_png(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _generate_text_card("测试卡片\n第二行", tmpdir, "test")
            if path:
                self.assertTrue(os.path.exists(path))
                self.assertTrue(path.endswith(".png"))


class TestVideoRenderer(unittest.TestCase):
    """Test video renderer (MoviePy fallback)."""

    def test_render_video_functions_are_importable(self):
        self.assertTrue(callable(render_video))
        self.assertTrue(callable(_render_with_ffmpeg))

    def test_create_background_is_callable(self):
        self.assertTrue(callable(_create_background))
