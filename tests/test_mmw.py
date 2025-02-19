# allow importing of local signalbot
import sys
import os
current_dir = __file__
path_to_append = os.path.join(current_dir, "../../signalbot_local/")
if os.path.exists(path_to_append):
    sys.path.append(path_to_append)
    print(f"Appended {path_to_append} to sys.path")
else:
    print(f"Path {path_to_append} does not exist")

import unittest
from unittest.mock import patch
import logging
from signalbot import Command, Context, triggered
from signalbot.utils import chat, ChatTestCase, SendMessagesMock, ReceiveMessagesMock
from run import PingCommand, LOGMSG

class mmwTest(ChatTestCase):
    def setUp(self):
        super().setUp()
        group = {"id": "asdf", "name": "Test"}
        self.signal_bot._groups_by_internal_id = {"group_id1=": group}
        self.signal_bot.groups = [{"internal_id": "group_id1=", "name": "fake group"}]
        self.signal_bot.register(PingCommand(), contacts=True, groups=True)

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_mmw_help(self, receive_mock, send_mock):
        receive_mock.define(["#mmw.help"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual( "mmw help" in send_mock.call_args_list[0].args[1], True )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_mmw_basic(self, receive_mock, send_mock):
        receive_mock.define(["#mmw test"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual( "exception" in send_mock.call_args_list[0].args[1], False )

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_mmw_complex(self, receive_mock, send_mock):
        text = "#mmw dunno if anyone except cav is following along at home, but there is now a devel branch which has automated tests. " \
               "if you write a new handler, you can also write a new test. there are less restrictions on this devel branch, and every time " \
               "to push it will run all the tests.\n\n" \
               "there is a really good chance that if you pass the tests then your handler probably works.\n" \
               "https://github.com/jamesoncollins/turbo-bot/tree/devel"
        receive_mock.define([text])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual( "exception" in send_mock.call_args_list[0].args[1], False )
        print(send_mock.call_args_list[0].args[1])

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_mmw_recall(self, receive_mock, send_mock):
        receive_mock.define(["#mmw"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual( "exception" in send_mock.call_args_list[0].args[1], False )
        print(send_mock.call_args_list[0].args[1])

if __name__ == "__main__":
    unittest.main()