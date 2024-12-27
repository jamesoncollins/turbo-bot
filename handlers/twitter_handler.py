# handlers/twitter_handler.py
import yt_dlp
from handlers.base_handler import BaseHandler

class TwitterHandler(BaseHandler):
    ALLOWED_DOMAINS = ["twitter.com", "x.com"]

    def can_handle(self) -> bool:
        url = self.extract_url(self.input_str)
        return url and self.is_url_in_domains(url, self.ALLOWED_DOMAINS)

    def get_attachments(self) -> list:
        url = self.extract_url(self.input_str)
        video_content = self.download_video(url)
        if video_content:
            return [BaseHandler.file_to_base64(video_content)]
        return []

    def get_message(self) -> str:
        return "Downloaded video content from Twitter/X."

    def download_video(self, url: str) -> str:
        """
        Downloads the video from a Twitter or X post URL using yt_dlp.

        Args:
            url (str): The URL of the Twitter or X post.

        Returns:
            str: The path to the downloaded video file, or an empty string if download fails.
        """
        filename = "downloaded_video.mp4"
        ydl_opts = {
            'outtmpl': filename,
            'format': 'bestvideo+bestaudio/best',
            'quiet': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return filename
        except Exception as e:
            print(f"Error downloading video: {e}")
        return ""

    @staticmethod
    def get_name() -> str:
        return "TwitterHandler"
