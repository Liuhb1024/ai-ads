import unittest

from app.share_text import ShareTextError, extract_supported_url


DOUYIN_SHARE_TEXT = (
    "3.89 09/30 hoD:/ :4pm Q@k.cN 夯爆了家人们，好自在这波真赢麻了，"
    "当你还在线下高价卖好自在的时候，别人早在这里拿下整整30瓶了"
    "# 元气森林 # 自律 # 好喝不贵 # 好物推荐 # 饮料 【广告】  "
    "https://v.douyin.com/zQB8XLGqE4I/ 复制此链接，打开Dou音搜索，直接观看视频！"
)


class ExtractSupportedUrlTests(unittest.TestCase):
    def test_extracts_url_from_full_douyin_share_text(self):
        self.assertEqual(
            extract_supported_url(DOUYIN_SHARE_TEXT),
            "https://v.douyin.com/zQB8XLGqE4I/",
        )

    def test_keeps_direct_supported_url(self):
        self.assertEqual(
            extract_supported_url("https://www.youtube.com/watch?v=abc123"),
            "https://www.youtube.com/watch?v=abc123",
        )

    def test_trims_chinese_and_ascii_punctuation(self):
        self.assertEqual(
            extract_supported_url("看看这个：https://b23.tv/abc123，真的不错"),
            "https://b23.tv/abc123",
        )

    def test_rejects_text_without_url(self):
        with self.assertRaises(ShareTextError):
            extract_supported_url("这是一段没有链接的分享文案")

    def test_rejects_unsupported_host(self):
        with self.assertRaises(ShareTextError):
            extract_supported_url("https://example.com/video/123")


if __name__ == "__main__":
    unittest.main()
