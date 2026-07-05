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
from unittest.mock import AsyncMock, patch
import logging
from signalbot import SignalBot, Command, Context, triggered
from signalbot.utils import mock_chat as chat, ChatTestCase, SendMessagesMock, ReceiveMessagesMock
from attachment_output import install_send_attachment_capture
from run import TurboBotCommand, LOGMSG


class TurboTestCase(unittest.IsolatedAsyncioTestCase, ChatTestCase):
    async def asyncSetUp(self):
        install_send_attachment_capture(SendMessagesMock)
        await super().asyncSetUp()
        self.setup()
        group = {
            "id": ChatTestCase.group_id,
            "internal_id": ChatTestCase.group_internal_id,
            "name": ChatTestCase.group_name,
        }
        self.signal_bot._signal.get_groups = AsyncMock(return_value=[group])
        self.signal_bot._groups_by_internal_id = {ChatTestCase.group_internal_id: group}
        self.signal_bot.groups = [group]
        self.signal_bot.register(TurboBotCommand(), contacts=True, groups=True)
        await self.signal_bot._resolve_commands()
