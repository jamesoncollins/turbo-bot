import os
from signalbot import SignalBot, Command, Context
import re
import time
import base64

from utils import *

LOGMSG = "----TURBOBOT----\n"

class PingCommand(Command):
    async def handle(self, c: Context):
        groupId = None
        try:
            groupId = c.message.group
            groupId = groupId.replace("/", "-")
        except:
            pass

        msg = c.message.text
        sourceName = c.message.raw_message["envelope"]["sourceName"]
        sourceNumber = c.message.raw_message["envelope"]["sourceNumber"]

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
        elif (url := is_youtube_domain(msg)):
            print("is youtube url " + url)
            if (fname:=download_youtube_video(url)):
                await c.reply( LOGMSG + "YouTube URL: " + url, base64_attachments=[file_to_base64(fname)])
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
        elif "#gpt" in msg:
            print("is gpt")
            query =  msg.replace("#gpt", "") 
            res = submit_gpt(query)
            await c.reply(LOGMSG + res)
        elif "#mmw" == msg and groupId:
            print("is mmw")
            mmw = print_file(f"mmw{groupId}.txt")
            await c.reply( LOGMSG + "History: \n" + mmw)            
        elif "#mmw" in msg and groupId:
            print("is mmw")
            mmw = sourceName + "(" + sourceNumber + "): " + msg
            await c.reply(LOGMSG + mmw)
            with open(f"mmw{groupId}.txt", "a") as file:
                file.write(mmw+"\n")
        elif msg == "#":
            print("is hash")
            await c.reply( LOGMSG + "I am here.")            
        elif msg == "#turboboot":
            print("is reboot")
            await c.reply( LOGMSG + "turbobot rebooting...")
            quit()          
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
    
    
    
