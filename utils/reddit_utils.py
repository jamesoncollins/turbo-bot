from utils.misc_utils import *
from utils.video_scrape_utils import *
from redvid import Downloader

import os
import re
import requests
from urllib.parse import urlparse, urlunparse


REDDIT_CANONICAL_HOST = "www.reddit.com"
REDDIT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
REDDIT_URL_RE = re.compile(
    r"https?://(?:[A-Za-z0-9-]+\.)?(?:reddit\.com|redd\.it)/[^\s<>\]\)]+",
    re.IGNORECASE,
)
REDDIT_COMMENTS_RE = re.compile(r"/comments/([A-Za-z0-9_]+)/?", re.IGNORECASE)
REDDIT_SHARE_RE = re.compile(r"/r/[^/]+/s/[A-Za-z0-9_%-]+/?", re.IGNORECASE)


def _strip_url_noise(url):
    return url.rstrip(".,!?;:)]}'\"")


def _canonical_reddit_comments_url(post_id):
    return f"https://{REDDIT_CANONICAL_HOST}/comments/{post_id}/"


def _resolve_reddit_redirect(url):
    response = requests.get(
        url,
        headers=REDDIT_REQUEST_HEADERS,
        allow_redirects=True,
        timeout=10,
    )
    response.raise_for_status()
    return response.url


def normalize_reddit_url(url):
    if not url:
        return None

    url = _strip_url_noise(url.strip())
    parsed_url = urlparse(url if urlparse(url).scheme else f"https://{url}")
    host = parsed_url.netloc.lower().split(":")[0]

    if host == "redd.it":
        post_id = parsed_url.path.strip("/").split("/", 1)[0]
        return _canonical_reddit_comments_url(post_id) if post_id else None

    if host.endswith("reddit.com"):
        comments_match = REDDIT_COMMENTS_RE.search(parsed_url.path)
        if comments_match:
            return _canonical_reddit_comments_url(comments_match.group(1))

        if REDDIT_SHARE_RE.fullmatch(parsed_url.path):
            try:
                return normalize_reddit_url(_resolve_reddit_redirect(url))
            except Exception as ex:
                print(f"Reddit share link normalization failed: {ex}")

        return urlunparse(("https", REDDIT_CANONICAL_HOST, parsed_url.path, "", "", ""))

    return None

def is_reddit_domain(msg):
    reddit_match = REDDIT_URL_RE.search(msg)
    if reddit_match:
        reddit_url = normalize_reddit_url(reddit_match.group(0))
        if reddit_url:
            print("is reddit url")
            return reddit_url
    else:
        #print("is NOT reddit url")
        return None
 
def is_shutdown_exception(ex):
    return isinstance(ex, (KeyboardInterrupt, SystemExit, GeneratorExit))


def download_reddit_video_tryall_b64(url):
    normalized_url = normalize_reddit_url(url)
    urls_to_try = [normalized_url or url]
    if url not in urls_to_try:
        urls_to_try.append(url)

    for candidate_url in urls_to_try:
        try:
            if (fname := download_reddit_video(candidate_url)):
                return file_to_base64(fname)
        except Exception as ex:
            print(f"Reddit yt-dlp/redvid download failed: {ex}")

        try:
            if (video_b64 := get_video_as_base64(candidate_url)):
                return video_b64
        except Exception as ex:
            print(f"Reddit HTML scrape download failed: {ex}")
    
    return None


def download_reddit_video(url):
    url = normalize_reddit_url(url) or url
    fname = "reddit.mp4"

    if (yt_dlp_filename := download_reddit_video_with_ytdlp(url, fname)):
        return yt_dlp_filename

    return download_reddit_video_with_redvid(url, fname)


def download_reddit_video_with_ytdlp(url, fname="reddit.mp4"):
    try:
        from handlers.twitter_handler import download_video

        url = normalize_reddit_url(url) or url
        return download_video(
            url,
            max_filesize_mb=90,
            suggested_filename=os.path.splitext(fname)[0],
        )
    except Exception as ex:
        print(f"yt-dlp reddit download failed: {ex}")
        return None


def download_reddit_video_with_redvid(url, fname="reddit.mp4"):
    try:
        os.remove(fname)
    except FileNotFoundError:
        print('thats fine')

    try:        
        reddit = Downloader(max_q=True) 
        reddit.url = normalize_reddit_url(url) or url
        reddit.filename = fname
        reddit.download()
        return os.path.abspath(fname)
    except BaseException as ex:
        if is_shutdown_exception(ex):
            raise
        print(ex)
        return None
        
