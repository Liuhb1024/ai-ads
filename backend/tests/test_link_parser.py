import unittest

from services.link_parser import _video_play_url
from services.frame_extractor import _parse_showinfo_timestamps


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


if __name__ == "__main__":
    unittest.main()
