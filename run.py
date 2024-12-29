import os
import sys
from signalbot import SignalBot, Command, Context
import re
import time
import base64
from handlers.base_handler import BaseHandler

from utils import *

LOGMSG = "----TURBOBOT----\n"

class PingCommand(Command):
    async def handle(self, c: Context):

        msg = c.message.text

        if msg is None:
            print("Message was None")
        elif msg == "Ping":
            print("is ping")
            await c.reply( LOGMSG + "Pong")
        elif (url := is_reddit_domain(msg)):
            print("is reddit url")
            video_b64 = download_reddit_video_tryall_b64(url)            
            if (video_b64):
                await c.reply( LOGMSG + "Reddit URL: " + url, base64_attachments=[video_b64])
        elif "instagram.com" in msg:
            print("is insta")
            url = extract_url(msg, "instagram.com")
            video_b64 = download_instagram_video_as_b64(url)
            await c.reply( LOGMSG + "IntsgramURL: " + url, base64_attachments=[video_b64])  
        elif (tickers := extract_ticker_symbols(msg)):
            print("is ticker")
            plot_b64 = plot_stock_data_base64(tickers)
            summary = get_stock_summary( convert_to_get_stock_summary_input(tickers) )
            await c.reply( LOGMSG + summary, base64_attachments=[plot_b64])  
        elif msg == "#":
            print("is hash")
            await c.reply( LOGMSG + "I am here.")            
        elif msg == "#turboboot":
            print("is reboot")
            await c.reply( LOGMSG + "turbobot rebooting...")
            sys.exit(1)
        else:
            handler_classes = BaseHandler.get_all_handlers()
            for handler_class in handler_classes:
                try:
                    handler = handler_class(msg)
                    handler.assign_context(c)
                    if handler.can_handle():
                        print("Handler Used:", handler_class.get_name())
                        await c.reply( LOGMSG + handler.get_message(), base64_attachments=handler.get_attachments() ) 
                        #return
                except Exception as e:
                    print(f"Handler exception: {e}")
        return


if __name__ == "__main__":
    bot = SignalBot({
        "signal_service": "signal-cli:8181",
        "phone_number": os.environ["BOT_NUMBER"]
    })
    bot.register(PingCommand()) # all contacts and groups
    #bot.register(PingCommand(), contacts=[ os.environ["BOT_NUMBER"]], groups=False)
    #bot.register(PingCommand(), contacts=False, groups=[os.environ['GROUP_NAME']])
    bot.start()
    
    
    
