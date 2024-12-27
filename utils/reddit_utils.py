from utils.misc_utils import *
from utils.video_scrape_utils import *
from redvid import Downloader

import re
import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup

# Function to convert a shareable Reddit link to the full comments link
def convert_shareable_to_comments_link(post_url):
    # Use regex to extract the subreddit and the post ID from the shareable URL
    match = re.match(r'https://www.reddit.com/r/([^/]+)/s/([a-zA-Z0-9]+)/?', post_url)
    
    if match:
        subreddit = match.group(1)  # Subreddit name
        post_id = match.group(2)    # Post ID
        
        # Construct the Reddit post URL
        full_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/"

        # Use requests to follow the redirection from the shareable URL
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(post_url, headers=headers, allow_redirects=True)

        # If the request was successful and the page was redirected
        if response.status_code == 200:
            redirected_url = response.url
            print(f"Redirected to full post URL: {redirected_url}")

            # Now fetch the post page from the redirected URL
            response = requests.get(redirected_url, headers=headers)
            if response.status_code == 200:
                # Use BeautifulSoup to parse the HTML content of the post page
                soup = BeautifulSoup(response.text, 'html.parser')
                post_title_tag = soup.find('h1')
                
                if post_title_tag:
                    post_title = post_title_tag.get_text()
                    
                    # Format the post title to be URL-safe
                    post_title_url = post_title.lower().replace(' ', '_').replace('/', '_').replace(':', '').replace('?', '').replace('&', '').replace('!', '')
                    
                    # Build the full URL with the post title and query parameters
                    base_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/{post_title_url}/"
                    query_params = {
                        "share_id": "6eF8RWTZIOBIi-ZY9Csky",  # Example, adjust this if needed
                        "utm_content": "1",
                        "utm_medium": "ios_app",
                        "utm_name": "ioscss",
                        "utm_source": "share",
                        "utm_term": "1"
                    }
                    full_url_with_params = base_url + "?" + urlencode(query_params)
                    return full_url_with_params
                else:
                    print("Post title not found on the page.")
                    return None
            else:
                print(f"Failed to retrieve redirected post page. Status code: {response.status_code}")
                return None
        else:
            print(f"Failed to follow redirection. Status code: {response.status_code}")
            return None
    else:
        print("Invalid shareable URL format.")
        return None

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
        
