from utils.misc_utils import *
import requests
from bs4 import BeautifulSoup
import os
import hashlib
import tempfile

# Where to store cached videos
CACHE_DIR = "video_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Hash function to make filenames safe and unique
def url_to_cache_filename(url):
    return hashlib.sha256(url.encode()).hexdigest() + ".mp4"

# Function to download the video
def download_video(url, save_path):
    response = requests.get(url, stream=True)
    with open(save_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

# Function to extract the video URL from a Reddit post
def get_video_url(post_url):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    response = requests.get(post_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        video_tag = soup.find('video')
        if video_tag:
            return video_tag['src']
    return None

# Function to download video and return it as a base64 string, with caching
def get_video_as_base64(post_url):
    video_url = get_video_url(post_url)
    if not video_url:
        print("No video found in the post.")
        return None

    # Get the cache file path
    cache_filename = url_to_cache_filename(video_url)
    cached_path = os.path.join(CACHE_DIR, cache_filename)

    # Use cache if available
    if os.path.exists(cached_path):
        print(f"Using cached video: {cached_path}")
    else:
        print(f"Downloading video from {video_url}...")
        download_video(video_url, cached_path)

    # Convert the (cached or downloaded) video to base64
    print("Converting video to base64...")
    return file_to_base64(cached_path)

# Example usage
if __name__ == "__main__":
    post_url = input("Enter the Reddit post URL: ")
    video_b64 = get_video_as_base64(post_url)

    if video_b64:
        print("Video successfully converted to base64!")
        print("Base64 String: ", video_b64[:100] + " ...")
    else:
        print("Failed to retrieve video as base64.")
