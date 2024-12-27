from utils.misc_utils import *
from utils.video_scrape_utils import *
from redvid import Downloader
import re
from urllib.parse import urlparse, parse_qs, urlencode

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
 
def download_reddit_video_tryall_b64(url):

    try:
        if (fname:=download_reddit_video(url)):
            return file_to_base64(fname)
    except:
        pass
    
    try:
        if (video_b64:=get_video_as_base64(url)):
            return video_b64
    except:
        pass
    
    url = convert_shareable_to_comments_link(url)
    
    try:
        if (fname:=download_reddit_video(url)):
            return file_to_base64(fname)
    except:
        pass
    
    try:
        if (video_b64:=get_video_as_base64(url)):
            return video_b64
    except:
        pass
    
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
        
# Function to convert a shareable Reddit link to the full comments link
def convert_shareable_to_comments_link(post_url):
    # Use regex to extract the post ID and the subreddit from the URL
    match = re.match(r'https://www.reddit.com/r/([^/]+)/s/([a-zA-Z0-9]+)/?', post_url)
    
    if match:
        subreddit = match.group(1)  # Subreddit name
        post_id = match.group(2)    # Post ID
        
        # Rebuild the URL to the comments section
        base_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/"
        
        # Construct the full URL with the necessary query parameters (this part is assumed from your example URL)
        query_params = {
            "share_id": "6eF8RWTZIOBIi-ZY9Csky",  # Example, adjust this if needed
            "utm_content": "1",
            "utm_medium": "ios_app",
            "utm_name": "ioscss",
            "utm_source": "share",
            "utm_term": "1"
        }
        
        # Append query parameters to the base URL
        full_url = base_url + "?" + urlencode(query_params)
        return full_url
    else:
        return None