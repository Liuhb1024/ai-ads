import unittest
from unittest.mock import AsyncMock, patch

from services.link_parser import (
    _parse_kuaishou,
    _parse_shipinhao,
    _parse_xiaohongshu,
    _video_play_url,
)
from services.frame_extractor import _parse_showinfo_timestamps

XHS_INITIAL_STATE = '<html><script>window.__INITIAL_STATE__={"note":{"noteDetailMap":{"abc123":{"note":{"title":"测评笔记标题","desc":"详细的测评描述","user":{"nickname":"美妆达人"},"imageList":[{"url":"https://example.com/thumb.jpg"}],"type":"normal"}}}}}</script></html>'

XHS_SHORT_HTML = '<html><script>window.__INITIAL_STATE__={"note":{"noteDetailMap":{"xyz789":{"note":{"title":"短链接测试笔记","desc":"短链描述","user":{"nickname":"测试用户"},"imageList":[]}}}}}</script></html>'

_KS_PAD = "x" * 120
KS_JSON_HTML = f'<html><script>{{"photoId":"ks001","caption":"快手测试视频","authorName":"快手创作者","coverUrl":"https://example.com/ks_cover.jpg","_pad":"{_KS_PAD}"}}</script></html>'

SHIPINHAO_META_HTML = """<html>
<head>
<meta property="og:title" content="视频号测试视频">
<meta property="og:image" content="https://example.com/sp_cover.jpg">
<meta property="og:description" content="视频号视频描述">
</head></html>"""

SHIPINHAO_EMPTY_HTML = """<html><head></head><body></body></html>"""


class DouyinVideoUrlTests(unittest.TestCase):
    def test_extracts_first_play_address(self):
        video = {
            "play_addr": {
                "url_list": [
                    "https://example.douyinvod.com/video-one",
                    "https://example.douyinvod.com/video-two",
                ]
            }
        }
        self.assertEqual(_video_play_url(video), "https://example.douyinvod.com/video-one")

    def test_supports_h264_fallback(self):
        video = {"play_addr_h264": {"url_list": ["https://example.com/h264"]}}
        self.assertEqual(_video_play_url(video), "https://example.com/h264")

    def test_parses_ffmpeg_frame_timestamps(self):
        stderr = (
            "[Parsed_showinfo_1] n:0 pts:1024 pts_time:1.024 pos:0\n"
            "[Parsed_showinfo_1] n:1 pts:5500 pts_time:5.5 pos:1\n"
        )
        self.assertEqual(_parse_showinfo_timestamps(stderr), [1.024, 5.5])


class XiaohongshuParserTests(unittest.IsolatedAsyncioTestCase):
    async def test_extracts_from_initial_state(self):
        with patch("services.link_parser._fetch_page", AsyncMock(return_value=(XHS_INITIAL_STATE, "https://www.xiaohongshu.com/explore/abc123"))):
            result = await _parse_xiaohongshu("https://xhslink.com/abc")
        self.assertTrue(result.parsed)
        self.assertEqual(result.platform, "小红书")
        self.assertEqual(result.title, "测评笔记标题")
        self.assertEqual(result.description, "详细的测评描述")
        self.assertEqual(result.author, "美妆达人")
        self.assertEqual(result.thumbnail_url, "https://example.com/thumb.jpg")

    async def test_extracts_from_short_link_redirect(self):
        with patch("services.link_parser._fetch_page", AsyncMock(return_value=(XHS_SHORT_HTML, "https://www.xiaohongshu.com/discovery/item/xyz789"))):
            result = await _parse_xiaohongshu("https://xhslink.com/xyz")
        self.assertTrue(result.parsed)
        self.assertEqual(result.title, "短链接测试笔记")
        self.assertEqual(result.author, "测试用户")

    async def test_handles_timeout(self):
        with patch("services.link_parser._fetch_page", AsyncMock(side_effect=__import__("httpx").TimeoutException("timeout"))):
            result = await _parse_xiaohongshu("https://xhslink.com/to")
        self.assertFalse(result.parsed)
        self.assertIn("超时", result.error)


class KuaishouParserTests(unittest.IsolatedAsyncioTestCase):
    async def test_extracts_from_json_blocks(self):
        with patch("services.link_parser._fetch_page", AsyncMock(return_value=(KS_JSON_HTML, "https://www.kuaishou.com/short-video/ks001"))):
            result = await _parse_kuaishou("https://v.kuaishou.com/xxx")
        self.assertTrue(result.parsed)
        self.assertEqual(result.platform, "快手")
        self.assertEqual(result.title, "快手测试视频")
        self.assertEqual(result.author, "快手创作者")
        self.assertEqual(result.thumbnail_url, "https://example.com/ks_cover.jpg")

    async def test_handles_timeout(self):
        with patch("services.link_parser._fetch_page", AsyncMock(side_effect=__import__("httpx").TimeoutException("timeout"))):
            result = await _parse_kuaishou("https://v.kuaishou.com/to")
        self.assertFalse(result.parsed)
        self.assertIn("超时", result.error)


class ShipinhaoParserTests(unittest.IsolatedAsyncioTestCase):
    async def test_extracts_meta_tags(self):
        with patch("services.link_parser._fetch_page", AsyncMock(return_value=(SHIPINHAO_META_HTML, "https://channels.weixin.qq.com/web/pages/feed?v=123"))):
            result = await _parse_shipinhao("https://channels.weixin.qq.com/xxx")
        self.assertTrue(result.parsed)
        self.assertEqual(result.platform, "视频号")
        self.assertEqual(result.title, "视频号测试视频")
        self.assertEqual(result.thumbnail_url, "https://example.com/sp_cover.jpg")
        self.assertEqual(result.description, "视频号视频描述")

    async def test_returns_unparsed_on_empty_page(self):
        with patch("services.link_parser._fetch_page", AsyncMock(return_value=(SHIPINHAO_EMPTY_HTML, "https://channels.weixin.qq.com/empty"))):
            result = await _parse_shipinhao("https://channels.weixin.qq.com/empty")
        self.assertFalse(result.parsed)

    async def test_handles_timeout(self):
        with patch("services.link_parser._fetch_page", AsyncMock(side_effect=__import__("httpx").TimeoutException("timeout"))):
            result = await _parse_shipinhao("https://channels.weixin.qq.com/to")
        self.assertFalse(result.parsed)
        self.assertIn("超时", result.error)


if __name__ == "__main__":
    unittest.main()
