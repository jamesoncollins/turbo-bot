from utils.misc_utils import *

import requests
from bs4 import BeautifulSoup
import os
import tempfile

# Function to download the video
def download_video(url, save_path):
    response = requests.get(url, stream=True)
    with open(save_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

# Function to extract the video URL from a Reddit post
def get_video_url(post_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(post_url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the Reddit video URL in the HTML
        video_tag = soup.find('video')
        if video_tag:
            video_url = video_tag['src']
            return video_url
    
    return None

# Function to download video and return it as a base64 string
def get_video_as_base64(post_url):
    video_url = get_video_url(post_url)
    
    if video_url:
        # Define a temporary file to save the video
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file_path = tmp_file.name
            
            # Download the video to the temporary file
            print(f"Downloading video from {video_url}...")
            download_video(video_url, tmp_file_path)
            
            # Convert the downloaded video to a base64 string
            print(f"Converting video to base64...")
            video_b64 = file_to_base64(tmp_file_path)
            
            # Clean up the temporary file after conversion
            os.remove(tmp_file_path)
            
            return video_b64
    else:
        print("No video found in the post.")
        return None

# Example usage
if __name__ == "__main__":
    post_url = input("Enter the Reddit post URL: ")
    video_b64 = get_video_as_base64(post_url)
    
    if video_b64:
        print("Video successfully converted to base64!")
        print("Base64 String: ", video_b64[:100] + " ...")  # Display a snippet of the base64 string
    else:
        print("Failed to retrieve video as base64.")
