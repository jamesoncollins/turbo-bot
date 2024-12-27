from utils.misc_utils import *

import instaloader
import os

def download_instagram_video_as_b64(url: str, username: str = None, password: str = None):
    # Create an instance of the instaloader class
    L = instaloader.Instaloader()

    # Log in if username and password are provided
    if username and password:
        print("Logging in...")
        L.login(username, password)
    else:
        print("No login credentials provided. Downloading public content.")

    # Extract the post from the given URL
    post = instaloader.Post.from_url(L.context, url)

    # Check if the post is a video
    if post.is_video:
        # Download the video
        print(f"Downloading video from {url}")
        L.download_post(post, target="downloads")

        # Find the downloaded video file
        video_filename = None
        for filename in os.listdir("downloads"):
            if filename.endswith(".mp4"):  # Assuming video files are in mp4 format
                video_filename = os.path.join("downloads", filename)
                break
        
        if video_filename:
            # Convert the video to a base64 string using the existing file_to_base64 function
            video_b64 = file_to_base64(video_filename)
            print("Video successfully converted to base64.")
            return video_b64
        else:
            print("Failed to find downloaded video file.")
    else:
        print("The provided URL does not point to a video.")
        return None

# Example usage
if __name__ == "__main__":
    # Optionally provide Instagram credentials and the video URL
    username = input("Enter your Instagram username (or press Enter to skip): ")
    password = input("Enter your Instagram password (or press Enter to skip): ")
    url = input("Enter the Instagram video URL: ")

    # If no username/password is provided, those parameters will default to None
    video_b64_string = download_instagram_video_as_b64(url, username if username else None, password if password else None)
    
    if video_b64_string:
        print(f"Base64 encoded video: {video_b64_string[:100]}...")  # Show first 100 characters of the b64 string
