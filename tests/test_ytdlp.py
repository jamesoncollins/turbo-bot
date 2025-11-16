# allow importing of local signalbot
import sys
import os
current_dir = os.path.abspath(__file__)
current_dir = os.path.dirname(current_dir)
path_to_append = os.path.join(current_dir, "../signalbot_local/")
if os.path.exists(path_to_append):
    sys.path.append(path_to_append)
    print(f"Appended {path_to_append} to sys.path")
else:
    print(f"Path {path_to_append} does not exist")

import unittest
from unittest.mock import patch
import logging
from TurboTestCase import TurboTestCase
from signalbot import Command, Context, triggered
from signalbot.utils import chat, ChatTestCase, SendMessagesMock, ReceiveMessagesMock
from run import TurboBotCommand, LOGMSG

class TwitterHandlerTest(TurboTestCase):
    def setUp(self):
        super().setUp()

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_tiktok(self, receive_mock, send_mock):
        receive_mock.define(["https://tiktok.com/@underrated.simpsons/video/7410898661741251873"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(len(send_mock.call_args[1]['base64_attachments']), 1)
        
    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_bsky(self, receive_mock, send_mock):
        receive_mock.define(["https://bsky.app/profile/bubbaprog.lol/post/3lga5ktfrx22o"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(len(send_mock.call_args[1]['base64_attachments']), 1)        

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_x(self, receive_mock, send_mock):
        receive_mock.define(["https://x.com/SaveUSAKitty/status/1872667773484363883"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(len(send_mock.call_args[1]['base64_attachments']), 1)

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_youtube(self, receive_mock, send_mock):
        receive_mock.define(["https://www.youtube.com/watch?v=hj4TXUJadt4"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(len(send_mock.call_args[1]['base64_attachments']), 1)

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_youtube_short(self, receive_mock, send_mock):
        receive_mock.define(["https://www.youtube.com/shorts/hw3pZaVL9YQ"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(len(send_mock.call_args[1]['base64_attachments']), 1)

    # reddit test, not actually using ytdlp if its reddit.com, i think
    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_reddit(self, receive_mock, send_mock):
        receive_mock.define(["https://www.reddit.com/r/TikTokCringe/s/Z3w1KP6KAc"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(len(send_mock.call_args[1]['base64_attachments']), 1)
        
if __name__ == "__main__":
    unittest.main()