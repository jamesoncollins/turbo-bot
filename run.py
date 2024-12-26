import os
from signalbot import SignalBot, Command, Context
#from commands import PingCommand
import re
from instascrape import *
import time
import yfinance as yf
import matplotlib.pyplot as plt
import base64
from redvid import Downloader
from insta_share import Instagram
from pytube import YouTube 
from pprint import pprint

def get_insta_sessionid():
    insta = Instagram()
    insta.login(os.environ["INSTA_USERNAME"], os.environ["INSTA_PASSWORD"])

    sessionid = insta.session["session_id"]
    return sessionid

def download_youtube_video(link):
    # where to save 
    SAVE_PATH = "/tmp/youtube/" #to_do 

    try: 
        # object creation using YouTube 
        yt = YouTube(link) 
    except: 
        #to handle exception 
        print("Connection Error") 

    # Get all streams and filter for mp4 files
    mp4_streams = yt.streams.filter(file_extension='mp4').all()

    # get the video with the highest resolution
    d_video = mp4_streams[-1]

    try: 
        # downloading the video 
        d_video.download(output_path=SAVE_PATH)
        print('Video downloaded successfully!')
        return SAVE_PATH
    except: 
        print("Some Error!")
    
    return None

def download_reddit_video(url):
    fname = "reddit.mp4"
    
    try:
        os.remove(fname)
    except:
        print('thats fine')
    
    try:        
        reddit = Downloader(max_q=True) 
        reddit.url = url
        reddit.filename = fname
        reddit.download()
        return "//root//git//turbo-bot//" + fname
    except Exception as ex:
        print(ex)
        return None

def file_to_base64(file_path):
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)
            base64_string = encoded_content.decode('utf-8')
            return base64_string
    except FileNotFoundError:
        return f"Error: File not found at path: {file_path}"


def download_insta(url):
    newurl = url
    #newurl = url + "?utm_source=ig_web_button_share_sheet"
    #newurl = re.sub(r'/+', '/', newurl)
    print("Trying to download from " + newurl)
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    fname = f"\\tmp\\reel\\file_{timestamp}.mp4"
    print("fname is " + fname)
    
    try:
        #SESSIONID = get_insta_sessionid()
        #headers = {"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.57",
        #       "cookie": f"sessionid={SESSIONID};"}
        msg_post = Reel(newurl)
        #msg_post.scrape(headers=headers)
        msg_post.scrape()
        msg_post.download(fp=fname)
    except Exception as ex:
        print(ex)
        return None
        
    return fname
    
    print('Downloaded Successfully.')

def extract_url(text, domain):
    pattern = r"https?://(?:www\.)?" + re.escape(domain) + r"(/[^\s]*)?"
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return None

def find_ticker(text):
  #pattern = r"\$[a-zA-Z]{3,4}"
  pattern = r"\$([a-zA-Z]{1,4})"
  matches = re.findall(pattern, text)
  return matches
  
def is_reddit_domain(msg):
    if "reddit.com" in msg:
        print("is reddit url")
        return extract_url(msg, "reddit.com")
    elif "redd.it" in msg: 
        print("is reddit url")
        return extract_url(msg, "redd.it")
    else:
        #print("is NOT reddit url")
        return None
 
def is_youtube_domain(msg):
    if "youtube.com" in msg:
        print("is youtube url")
        return extract_url(msg, "youtube.com")
    if "youtu.be" in msg:
        print("is youtube url")
        return extract_url(msg, "youtu.be")
    else:
        return None


def print_file(file_path):
    try:
        with open(file_path, 'r') as file:
            # Read the content of the file
            file_content = file.read()
            
            # Print the content
            #print(&quot;File Content:\n&quot;, file_content)
            
            return file_content

    except FileNotFoundError:
        pass #print(f&quot;File '{file_path}' not found.&quot;)
    except Exception as e:
        pass #print(f&quot;An error occurred: {e}&quot;)
        
    return None


class PingCommand(Command):
    async def handle(self, c: Context):
        groupId = None
        try:
            groupId = c.message.group
            groupId.replace("\\", "\\\\")
        except:
            pass
        msg = c.message.text
        #print(vars(c.message))
        sourceName = c.message.raw_message["envelope"]["sourceName"]
        sourceNumber = c.message.raw_message["envelope"]["sourceNumber"]
        #print(msg)
        if msg == "Ping":
            await c.send("Pong")
        elif (url := is_reddit_domain(msg)):
            print("is reddit url")
            if (fname:=download_reddit_video(url)):
                await c.reply("is reddit url " + url, base64_attachments=[file_to_base64(fname)])
        elif (url := is_youtube_domain(msg)):
            print("is youtube url " + url)
            if (fname:=download_youtube_video(url)):
                await c.reply("is youtube url " + url, base64_attachments=[file_to_base64(fname)])
        elif "instagram.com" in msg:
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
            stock = yf.Ticker(tickers[0])
            recent_data = yf.download(tickers, period="1y")            
            recent_data['Close'].plot()
            plt.savefig("//tmp//tick.png")
            await c.reply("plot", base64_attachments=[file_to_base64("//tmp//tick.png")])  
        elif "#mmw" == msg and groupId:
            mmw = print_file(f"mmw{groupId}.txt")
            await c.send("History: \n" + mmw)            
        elif "#mmw" in msg and groupId:
            await c.send(sourceName + "(" + sourceNumber + ")" " Says Mark My Words: \n" + msg)
            with open(f"mmw{groupId}.txt", "a") as file:
                file.write(msg+"\n")
        elif msg == "#":
            await c.send("I am here.")            
        elif msg == "#turboboot":
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
    
    
    
