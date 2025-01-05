import unittest
from unittest.mock import patch
import logging
from signalbot import Command, Context, triggered
from signalbot.utils import chat, ChatTestCase, SendMessagesMock, ReceiveMessagesMock
from run import PingCommand, LOGMSG

class InstaHandlerTest(ChatTestCase):
    def setUp(self):
        super().setUp()
        group = {"id": "asdf", "name": "Test"}
        self.signal_bot._groups_by_internal_id = {"group_id1=": group}
        self.signal_bot.register(PingCommand(), contacts=True, groups=True)

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_insta_url_1(self, receive_mock, send_mock):
        receive_mock.define(["https://www.instagram.com/reel/DDAKRLrvmeB/?igsh=MTk3OXdrdTljejJsNg%3D%3D"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(len(send_mock.call_args[1]['base64_attachments']), 1)


if __name__ == "__main__":
    unittest.main()