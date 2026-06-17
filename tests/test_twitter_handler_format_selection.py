import unittest
from unittest.mock import MagicMock, patch

from handlers.twitter_handler import (
    STREAM_CLIP_SECONDS,
    TwitterHandler,
    _base_ydl_opts,
    _is_live_stream,
    _is_unavailable_stream,
    _pick_best_download_format,
    _stream_tail_download_ranges,
    download_video,
)


class TwitterHandlerFormatSelectionTest(unittest.TestCase):
    def test_youtube_probe_uses_android_vr_client_for_split_formats(self):
        opts = _base_ydl_opts()

        self.assertEqual(
            opts["extractor_args"]["youtube"]["player_client"],
            ["android", "android_vr"],
        )

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

    @patch("handlers.twitter_handler.BaseHandler.file_to_base64", return_value="encoded")
    @patch("handlers.twitter_handler.download_video", return_value="video.mp4")
    @patch("handlers.twitter_handler.yt_dlp.YoutubeDL")
    def test_can_handle_reuses_probe_info_for_process_message(
        self, youtube_dl_cls, download_video_mock, _
    ):
        probe_info = {"formats": [{"format_id": "18"}]}
        ydl = MagicMock()
        ydl.extract_info.return_value = probe_info
        youtube_dl_cls.return_value = ydl

        handler = TwitterHandler("https://example.com/video")

        self.assertTrue(handler.can_handle())
        response = handler.process_message(None, None)

        self.assertEqual(ydl.extract_info.call_count, 1)
        download_video_mock.assert_called_once_with(
            "https://example.com/video",
            info=probe_info,
            stream_clip_seconds=None,
        )
        self.assertEqual(response["attachments"], ["encoded"])

    @patch("handlers.twitter_handler.BaseHandler.file_to_base64", return_value="encoded")
    @patch("handlers.twitter_handler.download_video", return_value="video.mp4")
    @patch("handlers.twitter_handler.yt_dlp.YoutubeDL")
    def test_live_stream_downloads_one_minute_clip_and_labels_stream(
        self, youtube_dl_cls, download_video_mock, _
    ):
        probe_info = {"is_live": True, "live_status": "is_live", "formats": []}
        ydl = MagicMock()
        ydl.extract_info.return_value = probe_info
        youtube_dl_cls.return_value = ydl

        handler = TwitterHandler("https://www.youtube.com/watch?v=live")

        self.assertTrue(handler.can_handle())
        response = handler.process_message(None, None)

        download_video_mock.assert_called_once_with(
            "https://www.youtube.com/watch?v=live",
            info=None,
            stream_clip_seconds=STREAM_CLIP_SECONDS,
        )
        self.assertIn("stream", response["message"])
        self.assertIn("1 minute", response["message"])
        self.assertEqual(response["attachments"], ["encoded"])

    @patch("handlers.twitter_handler.download_video")
    @patch("handlers.twitter_handler.yt_dlp.YoutubeDL")
    def test_upcoming_stream_is_not_downloaded(self, youtube_dl_cls, download_video_mock):
        probe_info = {"live_status": "is_upcoming", "formats": []}
        ydl = MagicMock()
        ydl.extract_info.return_value = probe_info
        youtube_dl_cls.return_value = ydl

        handler = TwitterHandler("https://www.youtube.com/watch?v=upcoming")

        self.assertTrue(handler.can_handle())
        response = handler.process_message(None, None)

        download_video_mock.assert_not_called()
        self.assertIn("stream", response["message"])
        self.assertEqual(response["attachments"], [])

    def test_stream_tail_range_uses_last_minute_of_known_duration(self):
        ranges = list(_stream_tail_download_ranges(60)({"duration": 125}, MagicMock()))

        self.assertEqual(ranges[0]["start_time"], 65)
        self.assertEqual(ranges[0]["end_time"], 125)

    @patch("handlers.twitter_handler.time.time", return_value=1_000)
    def test_stream_tail_range_falls_back_to_live_start_timestamp(self, _):
        ranges = list(_stream_tail_download_ranges(60)({"live_start_time": 950}, MagicMock()))

        self.assertEqual(ranges[0]["start_time"], 0)
        self.assertEqual(ranges[0]["end_time"], 50)

    def test_stream_status_helpers(self):
        self.assertTrue(_is_live_stream({"is_live": True}))
        self.assertTrue(_is_live_stream({"live_status": "is_live"}))
        self.assertTrue(_is_unavailable_stream({"live_status": "is_upcoming"}))
        self.assertTrue(_is_unavailable_stream({"live_status": "post_live"}))
        self.assertFalse(_is_live_stream({"live_status": "not_live"}))

    @patch("handlers.twitter_handler.os.rename")
    @patch("handlers.twitter_handler.convert_to_mp4", return_value="downloaded_video.mp4.in")
    @patch("handlers.twitter_handler.os.listdir", return_value=[])
    @patch("handlers.twitter_handler.yt_dlp.YoutubeDL")
    def test_download_video_applies_stream_range_options(
        self, youtube_dl_cls, _, __, ___
    ):
        ydl = MagicMock()
        ydl.__enter__.return_value = ydl
        ydl.__exit__.return_value = None
        ydl.extract_info.return_value = {"filepath": "downloaded_video.mp4"}
        youtube_dl_cls.return_value = ydl

        filename = download_video(
            "https://www.youtube.com/watch?v=live",
            info={"formats": []},
            stream_clip_seconds=STREAM_CLIP_SECONDS,
        )

        ydl_opts = youtube_dl_cls.call_args.args[0]
        self.assertEqual(filename, "downloaded_video.mp4")
        self.assertTrue(ydl_opts["live_from_start"])
        self.assertFalse(ydl_opts["force_keyframes_at_cuts"])
        self.assertTrue(callable(ydl_opts["download_ranges"]))


if __name__ == "__main__":
    unittest.main()
