# allow importing of local signalbot
import sys
import os
current_dir = os.path.abspath(__file__)
current_dir = os.path.dirname(current_dir)
path_to_append = os.path.join(current_dir, "../signalbot_local/src/")
if os.path.exists(path_to_append):
    sys.path.insert(0, path_to_append)
    print(f"Prepended {path_to_append} to sys.path")
else:
    print(f"Path {path_to_append} does not exist")

import unittest
from unittest.mock import patch
from TurboTestCase import TurboTestCase
from signalbot.utils import SendMessagesMock, ReceiveMessagesMock


TEST_VIDEO_ATTACHMENT = "mock-video-attachment"


class TwitterHandlerTest(TurboTestCase):
    def setUp(self):
        super().setUp()

    async def assert_ytdlp_url_routes_to_downloader(self, url, receive_mock, send_mock):
        probe_info = {
            "formats": [
                {
                    "format_id": "18",
                    "filesize": 1024,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                }
            ]
        }

        with patch("handlers.twitter_handler.yt_dlp.YoutubeDL") as youtube_dl_cls, \
                patch(
                    "handlers.twitter_handler.download_video",
                    return_value="downloaded_video.mp4",
                ) as download_video_mock, \
                patch(
                    "handlers.twitter_handler.BaseHandler.file_to_base64",
                    return_value=TEST_VIDEO_ATTACHMENT,
                ):
            ydl = youtube_dl_cls.return_value
            ydl.extract_info.return_value = probe_info

            receive_mock.define([url])
            await self.run_bot()

        ydl.extract_info.assert_called_once_with(url, download=False)
        download_video_mock.assert_called_once_with(
            url,
            info=probe_info,
            stream_clip_seconds=None,
        )
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(send_mock.call_args[1]["base64_attachments"], [TEST_VIDEO_ATTACHMENT])

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_tiktok_url_routes_to_ytdlp_downloader(self, receive_mock, send_mock):
        await self.assert_ytdlp_url_routes_to_downloader(
            "https://tiktok.com/@underrated.simpsons/video/7410898661741251873",
            receive_mock,
            send_mock,
        )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_bsky_url_routes_to_ytdlp_downloader(self, receive_mock, send_mock):
        await self.assert_ytdlp_url_routes_to_downloader(
            "https://bsky.app/profile/bubbaprog.lol/post/3lga5ktfrx22o",
            receive_mock,
            send_mock,
        )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_x_url_routes_to_ytdlp_downloader(self, receive_mock, send_mock):
        await self.assert_ytdlp_url_routes_to_downloader(
            "https://x.com/SaveUSAKitty/status/1872667773484363883",
            receive_mock,
            send_mock,
        )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_youtube_url_routes_to_ytdlp_downloader(self, receive_mock, send_mock):
        await self.assert_ytdlp_url_routes_to_downloader(
            "https://www.youtube.com/watch?v=hj4TXUJadt4",
            receive_mock,
            send_mock,
        )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_youtube_short_url_routes_to_ytdlp_downloader(self, receive_mock, send_mock):
        await self.assert_ytdlp_url_routes_to_downloader(
            "https://www.youtube.com/shorts/hw3pZaVL9YQ",
            receive_mock,
            send_mock,
        )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_instagram_reel_url_routes_to_ytdlp_downloader(self, receive_mock, send_mock):
        await self.assert_ytdlp_url_routes_to_downloader(
            "https://www.instagram.com/reel/DZuD9sTMeZU/",
            receive_mock,
            send_mock,
        )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_reddit_url_routes_to_reddit_downloader(self, receive_mock, send_mock):
        with patch(
            "run.download_reddit_video_tryall_b64",
            return_value=TEST_VIDEO_ATTACHMENT,
        ) as download_reddit_mock, \
                patch("utils.reddit_utils.requests.get") as get_mock:
            response = get_mock.return_value
            response.url = "https://www.reddit.com/r/TikTokCringe/comments/abc123/title/"
            response.raise_for_status.return_value = None

            receive_mock.define(["https://www.reddit.com/r/TikTokCringe/s/Z3w1KP6KAc"])
            await self.run_bot()

        download_reddit_mock.assert_called_once_with(
            "https://www.reddit.com/comments/abc123/"
        )
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(send_mock.call_args[1]["base64_attachments"], [TEST_VIDEO_ATTACHMENT])

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_old_reddit_url_routes_to_reddit_downloader(self, receive_mock, send_mock):
        url = "https://old.reddit.com/r/WNBAgossips/comments/1ukm1y4/she_finally_had_enough/"

        with patch(
            "run.download_reddit_video_tryall_b64",
            return_value=TEST_VIDEO_ATTACHMENT,
        ) as download_reddit_mock:
            receive_mock.define([url])
            await self.run_bot()

        download_reddit_mock.assert_called_once_with(
            "https://www.reddit.com/comments/1ukm1y4/"
        )
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(send_mock.call_args[1]["base64_attachments"], [TEST_VIDEO_ATTACHMENT])

if __name__ == "__main__":
    unittest.main()
