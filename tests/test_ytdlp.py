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
import logging
from TurboTestCase import TurboTestCase
from signalbot import Command, Context, triggered
from signalbot.utils import mock_chat as chat, ChatTestCase, SendMessagesMock, ReceiveMessagesMock
from run import TurboBotCommand, LOGMSG

class TwitterHandlerTest(TurboTestCase):
    def setUp(self):
        super().setUp()

    async def assert_ytdlp_url_sends_attachment(self, url, receive_mock, send_mock):
        with patch(
            "handlers.twitter_handler.TwitterHandler._probe_download_info",
            return_value={"formats": []},
        ) as probe_mock, patch(
            "handlers.twitter_handler.download_video",
            return_value="video.mp4",
        ) as download_mock, patch(
            "handlers.twitter_handler.BaseHandler.file_to_base64",
            return_value="encoded-video",
        ):
            receive_mock.define([url])
            await self.run_bot()

        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(len(send_mock.call_args[1]["base64_attachments"]), 1)
        probe_mock.assert_called_with(url)
        download_mock.assert_called_once()

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_tiktok(self, receive_mock, send_mock):
        await self.assert_ytdlp_url_sends_attachment(
            "https://tiktok.com/@underrated.simpsons/video/7410898661741251873",
            receive_mock,
            send_mock,
        )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_bsky(self, receive_mock, send_mock):
        await self.assert_ytdlp_url_sends_attachment(
            "https://bsky.app/profile/bubbaprog.lol/post/3lga5ktfrx22o",
            receive_mock,
            send_mock,
        )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_x(self, receive_mock, send_mock):
        await self.assert_ytdlp_url_sends_attachment(
            "https://x.com/SaveUSAKitty/status/1872667773484363883",
            receive_mock,
            send_mock,
        )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_youtube(self, receive_mock, send_mock):
        await self.assert_ytdlp_url_sends_attachment(
            "https://www.youtube.com/watch?v=hj4TXUJadt4",
            receive_mock,
            send_mock,
        )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_youtube_short(self, receive_mock, send_mock):
        await self.assert_ytdlp_url_sends_attachment(
            "https://www.youtube.com/shorts/hw3pZaVL9YQ",
            receive_mock,
            send_mock,
        )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_instagram_reel(self, receive_mock, send_mock):
        await self.assert_ytdlp_url_sends_attachment(
            "https://www.instagram.com/reel/DZuD9sTMeZU/",
            receive_mock,
            send_mock,
        )

    # reddit test, not actually using ytdlp if its reddit.com, i think
    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_reddit(self, receive_mock, send_mock):
        with patch("run.download_reddit_video_tryall_b64", return_value="encoded-video"):
            receive_mock.define(["https://www.reddit.com/r/TikTokCringe/s/Z3w1KP6KAc"])
            await self.run_bot()

        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(len(send_mock.call_args[1]["base64_attachments"]), 1)

if __name__ == "__main__":
    unittest.main()
