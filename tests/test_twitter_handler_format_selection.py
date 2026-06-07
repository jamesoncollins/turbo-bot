import unittest

from handlers.twitter_handler import _pick_best_download_format


class TwitterHandlerFormatSelectionTest(unittest.TestCase):
    def test_prefers_largest_muxed_format_under_limit(self):
        formats = [
            {"format_id": "small", "filesize": 10 * 1024 * 1024, "vcodec": "avc1", "acodec": "mp4a"},
            {"format_id": "best", "filesize": 80 * 1024 * 1024, "vcodec": "avc1", "acodec": "mp4a"},
            {"format_id": "too_big", "filesize": 120 * 1024 * 1024, "vcodec": "avc1", "acodec": "mp4a"},
        ]

        self.assertEqual(_pick_best_download_format(formats, 90), "best")

    def test_falls_back_to_mp4_video_plus_m4a_audio_pair_under_limit(self):
        formats = [
            {"format_id": "137", "ext": "mp4", "filesize": 100 * 1024 * 1024, "vcodec": "avc1", "acodec": "none"},
            {"format_id": "399", "ext": "mp4", "filesize": 60 * 1024 * 1024, "vcodec": "av01", "acodec": "none"},
            {"format_id": "248", "ext": "webm", "filesize": 50 * 1024 * 1024, "vcodec": "vp9", "acodec": "none"},
            {"format_id": "140", "ext": "m4a", "filesize": 20 * 1024 * 1024, "vcodec": "none", "acodec": "mp4a"},
            {"format_id": "251", "ext": "webm", "filesize": 10 * 1024 * 1024, "vcodec": "none", "acodec": "opus"},
        ]

        self.assertEqual(_pick_best_download_format(formats, 90), "399+140")

    def test_returns_none_when_no_under_limit_choice_exists(self):
        formats = [
            {"format_id": "137", "ext": "mp4", "filesize": 100 * 1024 * 1024, "vcodec": "avc1", "acodec": "none"},
            {"format_id": "140", "ext": "m4a", "filesize": 20 * 1024 * 1024, "vcodec": "none", "acodec": "mp4a"},
        ]

        self.assertIsNone(_pick_best_download_format(formats, 90))


if __name__ == "__main__":
    unittest.main()
