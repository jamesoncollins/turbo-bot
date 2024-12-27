from misc_utils import *
from redvid import Downloader

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