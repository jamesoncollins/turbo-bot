from utils.misc_utils import *
import instaloader
import os
import re
from handlers.base_handler import BaseHandler

class InstaHandler(BaseHandler):
    ALLOWED_DOMAINS = ["instagram.com", "www.instagram.com"]

    def can_handle(self) -> bool:
        url = self.extract_url(self.input_str)
        return url and self.is_url_in_domains(url, self.ALLOWED_DOMAINS)

    def process_message(self, msg, attachments):
        url = self.extract_url(self.input_str)
        video_content = download_instagram_video_as_b64(url)
        if video_content:
            return {
                "message": "Downloaded video content from Twitter/X.",
                "attachments": [video_content],
            }
        return []

    @staticmethod
    def get_name() -> str:
        return "Instagram Handler"
    
def download_instagram_video_as_b64(url: str, username: str = None, password: str = None):
    # Create an instance of the instaloader class
    L = instaloader.Instaloader()

    # Log in if username and password are provided
    if username and password:
        print("Logging in...")
        L.login(username, password)
    else:
        print("No login credentials provided. Downloading public content.")

    # Extract shortcode from the URL
    shortcode = None
    match = re.search(r"instagram\.com/(?:p|reel)/([^/?]+)", url) # Updated regex to handle both cases
    if match:
        shortcode = match.group(1)
    if not shortcode:
        print("Invalid Instagram URL. Unable to extract shortcode.")
        return None

    # Get the post using the shortcode
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
    except Exception as e:
        print(f"Error extracting post: {e}")
        return None

    # Check if the post is a video
    if post.is_video:
        # Define target download directory
        download_dir = "insta_dl"
        
        # Ensure the download directory exists
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            print(f"Created download directory: {download_dir}")
        
        # Delete the existing video file if it exists to ensure a fresh download
        for filename in os.listdir(download_dir):
            if filename.endswith(".mp4"):  # Assuming video files are in mp4 format
                os.remove(os.path.join(download_dir, filename))
                print(f"Existing video file {filename} removed to allow fresh download.")

        # Download the video
        print(f"Downloading video from {url}")
        L.download_post(post, target=download_dir)

        # Find the downloaded video file
        video_filename = None
        for filename in os.listdir(download_dir):
            if filename.endswith(".mp4"):  # Assuming video files are in mp4 format
                video_filename = os.path.join(download_dir, filename)
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

# # Example usage
# if __name__ == "__main__":
#     # Optionally provide Instagram credentials and the video URL
#     username = input("Enter your Instagram username (or press Enter to skip): ")
#     password = input("Enter your Instagram password (or press Enter to skip): ")
#     url = input("Enter the Instagram video URL: ")
#
#     # If no username/password is provided, those parameters will default to None
#     video_b64_string = download_instagram_video_as_b64(url, username if username else None, password if password else None)
#
#     if video_b64_string:
#         print(f"Base64 encoded video: {video_b64_string[:100]}...")  # Show first 100 characters of the b64 string