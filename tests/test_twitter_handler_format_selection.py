import unittest
from unittest.mock import MagicMock, patch

from handlers.twitter_handler import (
    STREAM_CLIP_SECONDS,
    TwitterHandler,
    _base_ydl_opts,
    _is_live_stream,
    _is_unavailable_stream,
    _pick_best_download_format,
    _signal_attachment_max_filesize_mb,
    _stream_tail_download_ranges,
    download_video,
)
from utils.misc_utils import _mp4_video_bitrate, convert_to_mp4


class TwitterHandlerFormatSelectionTest(unittest.TestCase):
    def test_transcode_bitrate_uses_input_size_when_smaller_than_max(self):
        input_size_bytes = 13 * 1024 * 1024
        duration_seconds = 60

        max_budget_bitrate = _mp4_video_bitrate(90 * 1024 * 1024, duration_seconds)
        input_size_bitrate = _mp4_video_bitrate(input_size_bytes, duration_seconds)

        self.assertEqual(input_size_bitrate, "1647k")
        self.assertNotEqual(input_size_bitrate, max_budget_bitrate)

    @patch("utils.misc_utils.os.path.getsize", return_value=12 * 1024 * 1024)
    @patch("utils.misc_utils.ffmpeg")
    def test_convert_to_mp4_targets_input_size_not_full_max_budget(self, ffmpeg_mock, _):
        input_size_bytes = 13 * 1024 * 1024
        ffmpeg_mock.probe.return_value = {
            "format": {
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                "duration": "60",
                "size": str(input_size_bytes),
            },
            "streams": [
                {"codec_type": "video", "width": 640, "height": 360},
            ],
        }
        ffmpeg_mock.input.return_value.output.return_value.run.return_value = None

        convert_to_mp4("downloaded_video.mp4.in", "downloaded_video.mp4", 90)

        output_kwargs = ffmpeg_mock.input.return_value.output.call_args.kwargs
        self.assertEqual(output_kwargs["video_bitrate"], "1647k")


    @patch("utils.misc_utils.ffmpeg")
    def test_convert_to_mp4_skips_iphone_compatible_mp4(self, ffmpeg_mock):
        ffmpeg_mock.probe.return_value = {
            "format": {
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                "duration": "60",
                "size": str(13 * 1024 * 1024),
            },
            "streams": [
                {"codec_type": "video", "codec_name": "h264", "width": 640, "height": 360},
                {"codec_type": "audio", "codec_name": "aac"},
            ],
        }

        result = convert_to_mp4("downloaded_video.mp4.in", "downloaded_video.mp4", 90)

        self.assertEqual(result, "downloaded_video.mp4.in")
        ffmpeg_mock.input.assert_not_called()

    @patch("utils.misc_utils.os.path.getsize", return_value=12 * 1024 * 1024)
    @patch("utils.misc_utils.ffmpeg")
    def test_convert_to_mp4_transcodes_mp4_with_unsupported_video_codec(self, ffmpeg_mock, _):
        ffmpeg_mock.probe.return_value = {
            "format": {
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                "duration": "60",
                "size": str(13 * 1024 * 1024),
            },
            "streams": [
                {"codec_type": "video", "codec_name": "av1", "width": 640, "height": 360},
                {"codec_type": "audio", "codec_name": "aac"},
            ],
        }
        ffmpeg_mock.input.return_value.output.return_value.run.return_value = None

        result = convert_to_mp4("downloaded_video.mp4.in", "downloaded_video.mp4", 90)

        self.assertEqual(result, "downloaded_video.mp4")
        output_kwargs = ffmpeg_mock.input.return_value.output.call_args.kwargs
        self.assertEqual(output_kwargs["vcodec"], "libx264")
        self.assertEqual(output_kwargs["acodec"], "aac")

    def test_youtube_probe_uses_android_vr_client_for_split_formats(self):
        opts = _base_ydl_opts()

        self.assertEqual(
            opts["extractor_args"]["youtube"]["player_client"],
            ["android", "android_vr"],
        )

    def test_signal_attachment_limit_defaults_to_normal_bot_target_size(self):
        with patch.dict("handlers.twitter_handler.os.environ", {}, clear=True):
            self.assertEqual(_signal_attachment_max_filesize_mb(), 60)

    def test_signal_attachment_limit_can_be_overridden(self):
        with patch.dict("handlers.twitter_handler.os.environ", {"YTDLP_SIGNAL_ATTACHMENT_MB": "12"}):
            self.assertEqual(_signal_attachment_max_filesize_mb(), 12)

    def test_prefers_largest_compatible_muxed_format_under_limit(self):
        formats = [
            {"format_id": "small", "ext": "mp4", "filesize": 10 * 1024 * 1024, "vcodec": "avc1", "acodec": "mp4a"},
            {"format_id": "best", "ext": "mp4", "filesize": 80 * 1024 * 1024, "vcodec": "avc1.64001f", "acodec": "mp4a.40.2"},
            {"format_id": "larger_av1", "ext": "mp4", "filesize": 85 * 1024 * 1024, "vcodec": "av01", "acodec": "mp4a"},
            {"format_id": "too_big", "ext": "mp4", "filesize": 120 * 1024 * 1024, "vcodec": "avc1", "acodec": "mp4a"},
        ]

        self.assertEqual(_pick_best_download_format(formats, 90), "best")

    def test_falls_back_to_compatible_mp4_video_plus_m4a_audio_pair_under_limit(self):
        formats = [
            {"format_id": "137", "ext": "mp4", "filesize": 100 * 1024 * 1024, "vcodec": "avc1", "acodec": "none"},
            {"format_id": "399", "ext": "mp4", "filesize": 60 * 1024 * 1024, "vcodec": "av01", "acodec": "none"},
            {"format_id": "398", "ext": "mp4", "filesize": 50 * 1024 * 1024, "vcodec": "avc1.4d401f", "acodec": "none"},
            {"format_id": "248", "ext": "webm", "filesize": 50 * 1024 * 1024, "vcodec": "vp9", "acodec": "none"},
            {"format_id": "140", "ext": "m4a", "filesize": 20 * 1024 * 1024, "vcodec": "none", "acodec": "mp4a.40.2"},
            {"format_id": "251", "ext": "webm", "filesize": 10 * 1024 * 1024, "vcodec": "none", "acodec": "opus"},
        ]

        self.assertEqual(_pick_best_download_format(formats, 90), "398+140")

    def test_falls_back_to_incompatible_format_when_no_compatible_choice_fits(self):
        formats = [
            {"format_id": "137", "ext": "mp4", "filesize": 100 * 1024 * 1024, "vcodec": "avc1", "acodec": "none"},
            {"format_id": "399", "ext": "mp4", "filesize": 60 * 1024 * 1024, "vcodec": "av01", "acodec": "none"},
            {"format_id": "140", "ext": "m4a", "filesize": 20 * 1024 * 1024, "vcodec": "none", "acodec": "mp4a"},
        ]

        self.assertEqual(_pick_best_download_format(formats, 90), "399+140")

    def test_uses_bitrate_estimate_when_formats_do_not_report_filesize(self):
        formats = [
            {
                "format_id": "dash-video",
                "ext": "mp4",
                "tbr": 294.306,
                "width": 1080,
                "height": 1920,
                "vcodec": "vp09.00.40.08.00.01.01.01.00",
                "acodec": "none",
            },
            {
                "format_id": "dash-audio",
                "ext": "m4a",
                "tbr": 78.57,
                "vcodec": "none",
                "acodec": "mp4a.40.5",
            },
        ]

        self.assertEqual(
            _pick_best_download_format(formats, 90, duration=57.05),
            "dash-video+dash-audio",
        )

    def test_uses_bitrate_rank_when_filesize_and_duration_are_missing(self):
        formats = [
            {
                "format_id": "lower-video",
                "ext": "mp4",
                "tbr": 224.386,
                "width": 720,
                "height": 1280,
                "vcodec": "vp09.00.31.08.00.01.01.01.00",
                "acodec": "none",
            },
            {
                "format_id": "higher-video",
                "ext": "mp4",
                "tbr": 294.306,
                "width": 1080,
                "height": 1920,
                "vcodec": "vp09.00.40.08.00.01.01.01.00",
                "acodec": "none",
            },
            {
                "format_id": "dash-audio",
                "ext": "m4a",
                "tbr": 78.57,
                "vcodec": "none",
                "acodec": "mp4a.40.5",
            },
        ]

        self.assertEqual(
            _pick_best_download_format(formats, 90),
            "higher-video+dash-audio",
        )

    def test_uses_video_and_audio_ext_when_codecs_are_missing(self):
        formats = [
            {
                "format_id": "unknown-video",
                "ext": "mp4",
                "video_ext": "mp4",
                "audio_ext": "none",
                "tbr": 224.386,
            },
            {
                "format_id": "dash-audio",
                "ext": "m4a",
                "video_ext": "none",
                "audio_ext": "m4a",
                "tbr": 78.57,
            },
        ]

        self.assertEqual(
            _pick_best_download_format(formats, 90, duration=57.05),
            "unknown-video+dash-audio",
        )

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
            max_filesize_mb=60,
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
            max_filesize_mb=60,
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

    @patch("handlers.twitter_handler.os.rename")
    @patch("handlers.twitter_handler.convert_to_mp4", return_value="downloaded_video.mp4.in")
    @patch("handlers.twitter_handler.os.listdir", return_value=[])
    @patch("handlers.twitter_handler.yt_dlp.YoutubeDL")
    def test_download_video_size_filter_allows_missing_filesize(
        self, youtube_dl_cls, _, __, ___
    ):
        ydl = MagicMock()
        ydl.__enter__.return_value = ydl
        ydl.__exit__.return_value = None
        ydl.extract_info.return_value = {"filepath": "downloaded_video.mp4"}
        youtube_dl_cls.return_value = ydl

        download_video(
            "https://www.instagram.com/reel/DZuD9sTMeZU/",
            info={
                "formats": [
                    {
                        "format_id": "dash-video",
                        "ext": "mp4",
                        "tbr": 294.306,
                        "width": 1080,
                        "height": 1920,
                        "vcodec": "vp09.00.40.08.00.01.01.01.00",
                        "acodec": "none",
                    },
                    {
                        "format_id": "dash-audio",
                        "ext": "m4a",
                        "tbr": 78.57,
                        "vcodec": "none",
                        "acodec": "mp4a.40.5",
                    },
                ]
            },
        )

        ydl_opts = youtube_dl_cls.call_args.args[0]
        ydl_opts["match_filter"]({"filesize": None, "filesize_approx": None})


if __name__ == "__main__":
    unittest.main()
