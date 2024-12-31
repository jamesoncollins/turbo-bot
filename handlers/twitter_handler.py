# handlers/twitter_handler.py
import yt_dlp
import os
from handlers.base_handler import BaseHandler

class FilenameCollectorPP(yt_dlp.postprocessor.common.PostProcessor):
    def __init__(self):
        super(FilenameCollectorPP, self).__init__(None)
        self.filenames = []

    def run(self, information):
        self.filenames.append(information["filepath"])
        return [], information

class TwitterHandler(BaseHandler):
    ALLOWED_DOMAINS = ["twitter.com", "x.com", "www.tiktok.com", "tiktok.com", "youtube.com", "youtu.be"]

    def can_handle(self) -> bool:
        url = self.extract_url(self.input_str)
        return url and self.is_url_in_domains(url, self.ALLOWED_DOMAINS)

    def get_attachments(self) -> list:
        url = self.extract_url(self.input_str)
        video_content = download_video(url)
        if video_content:
            return [BaseHandler.file_to_base64(video_content)]
        return []

    def get_message(self) -> str:
        return "Downloaded video content from Twitter/X."

    @staticmethod
    def get_name() -> str:
        return "TwitterHandler"
    
    
def download_video(url: str) -> str:
    """
    Downloads the video from a Twitter or X post URL using yt_dlp.

    Args:
        url (str): The URL of the Twitter or X post.

    Returns:
        str: The path to the downloaded video file, or an empty string if download fails.
    """
    filename = "downloaded_video.mp4"
    test = os.listdir("./")        
    for item in test:
        if item.startswith(filename):
            os.remove(os.path.join("./", item))    
    ydl_opts = {
        'outtmpl': filename,
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            #print(info)
            if info['duration'] > 900:
                raise("video too long")
            filename_collector = FilenameCollectorPP()
            ydl.add_post_processor(filename_collector)
            ydl.download([url])
        return filename_collector.filenames[0]
    except Exception as e:
        print(f"Error downloading video: {e}")
    return ""
