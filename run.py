import os
from signalbot import SignalBot, Command, Context
import re
import time
import base64

from utils import *

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

        if msg == "Ping":
            print("is ping")
            await c.send("Pong")
        elif (url := is_reddit_domain(msg)):
            print("is reddit url")
            if (fname:=download_reddit_video(url)):
                await c.reply("Reddit URL: " + url, base64_attachments=[file_to_base64(fname)])
        elif (url := is_youtube_domain(msg)):
            print("is youtube url " + url)
            if (fname:=download_youtube_video(url)):
                await c.reply("YouTube URL: " + url, base64_attachments=[file_to_base64(fname)])
        elif "instagram.com" in msg:
            print("is insta")
            url = extract_url(msg, "instagram.com")
            if url:
                fname = download_insta(url)
                if fname:
                    await c.send("got file")
                else:
                    await c.send("failed to download")
            else:
                await c.send("failed to get url")
        elif (tickers := find_ticker(msg)):
            print("is ticker")
            stock = yf.Ticker(tickers[0])
            recent_data = yf.download(tickers, period="1y")            
            recent_data['Close'].plot()
            plt.savefig("//tmp//tick.png")
            await c.reply("plot", base64_attachments=[file_to_base64("//tmp//tick.png")])  
        elif "#gpt" in msg:
            print("is gpt")
            query =  msg.replace("#gpt", "") 
            res = submit_gpt(query)
            await c.reply(res)
        elif "#mmw" == msg and groupId:
            print("is mmw")
            mmw = print_file(f"mmw{groupId}.txt")
            await c.send("History: \n" + mmw)            
        elif "#mmw" in msg and groupId:
            print("is mmw")
            mmw = sourceName + "(" + sourceNumber + "): " + msg
            await c.send(mmw)
            with open(f"mmw{groupId}.txt", "a") as file:
                file.write(mmw+"\n")
        elif msg == "#":
            print("is hash")
            await c.send("I am here.")            
        elif msg == "#turboboot":
            print("is reboot")
            await c.send("turbobot rebooting...")
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
    
    
    
