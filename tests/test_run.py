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
import os
import tempfile
from TurboTestCase import TurboTestCase
from signalbot import Command, Context, triggered
from signalbot.utils import chat, ChatTestCase, SendMessagesMock, ReceiveMessagesMock
from run import (
    TurboBotCommand,
    LOGMSG,
    BRANCH_SWITCH_EXIT_CODE,
    parse_branch_switch_command,
    request_branch_switch,
)

class RunTest(TurboTestCase):
    def setUp(self):
        super().setUp()

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_ping_pong(self, receive_mock, send_mock):
        receive_mock.define(["Ping"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(send_mock.call_args_list[0].args[1], LOGMSG + "Pong")

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_hash(self, receive_mock, send_mock):
        receive_mock.define(["#"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        response = send_mock.call_args_list[0].args[1]
        self.assertEqual( LOGMSG in response , True)
        self.assertEqual( "Machine:" in response , True)
        self.assertEqual( "Hostname:" in response , True)
        self.assertEqual( "OS:" in response , True)
        
    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_golf(self, receive_mock, send_mock):
        receive_mock.define(["#golf monday"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual( LOGMSG in send_mock.call_args_list[0].args[1] , True)
        
    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_ticker(self, receive_mock, send_mock):
        receive_mock.define(["$amd.5y"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_gpt_read(self, receive_mock, send_mock):
        receive_mock.define(["#gpt.read https://therationalleague.substack.com/p/why-maga-defends-everything-trump"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)

    def test_parse_branch_switch_command(self):
        self.assertEqual(parse_branch_switch_command("#branch devel"), "devel")
        self.assertEqual(parse_branch_switch_command("#branch feature/test-1"), "feature/test-1")
        self.assertEqual(parse_branch_switch_command(" #branch main "), "main")
        self.assertIsNone(parse_branch_switch_command("#branch"))
        self.assertIsNone(parse_branch_switch_command("#"))
        with self.assertRaises(ValueError):
            parse_branch_switch_command("#branch ../main")

    def test_request_branch_switch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            request_file = os.path.join(temp_dir, "branch_request.txt")
            with patch("run.BRANCH_REQUEST_FILE", request_file):
                request_branch_switch("devel")

            with open(request_file, "r", encoding="utf-8") as branch_request_file:
                self.assertEqual(branch_request_file.read(), "devel\n")

    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_branch_switch_requests_restart(self, receive_mock, send_mock):
        with tempfile.TemporaryDirectory() as temp_dir:
            request_file = os.path.join(temp_dir, "branch_request.txt")
            receive_mock.define(["#branch devel"])

            with patch("run.BRANCH_REQUEST_FILE", request_file):
                with self.assertRaises(SystemExit) as exit_context:
                    await self.run_bot()

            self.assertEqual(exit_context.exception.code, BRANCH_SWITCH_EXIT_CODE)
            self.assertEqual(send_mock.call_count, 1)
            self.assertEqual(
                send_mock.call_args_list[0].args[1],
                LOGMSG + "Switching to branch 'devel' and restarting...",
            )
            with open(request_file, "r", encoding="utf-8") as branch_request_file:
                self.assertEqual(branch_request_file.read(), "devel\n")

    @patch("run.get_current_branch_name", return_value="devel")
    @patch("signalbot.SignalAPI.send", new_callable=SendMessagesMock)
    @patch("signalbot.SignalAPI.receive", new_callable=ReceiveMessagesMock)
    async def test_branch_without_name_returns_current_branch(self, receive_mock, send_mock, current_branch_mock):
        receive_mock.define(["#branch"])
        await self.run_bot()
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(send_mock.call_args_list[0].args[1], LOGMSG + "Current branch: devel")

if __name__ == "__main__":
    unittest.main()
