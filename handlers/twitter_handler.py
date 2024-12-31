# handlers/twitter_handler.py
import yt_dlp
import os
from handlers.base_handler import BaseHandler

recent_video_cache = {} # TODO, manage the lifetime of this thing

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
        video_content = download_video_with_limit(url)
        if video_content:
            return [BaseHandler.file_to_base64(video_content)]
        return []

    def get_message(self) -> str:
        return "Downloaded video content from Twitter/X."

    @staticmethod
    def get_name() -> str:
        return "TwitterHandler"
    
    
def download_video(url: str) -> str:
    return download_video_with_limit(url)

def download_video_with_limit(url, max_filesize_mb=90, suggested_filename="downloaded_video.mp4"):
    """
    Downloads the best quality video below the specified file size limit.

    :param url: URL of the video to download
    :param max_filesize_mb: Maximum file size in megabytes
    :param suggested_filename: Suggested filename for the downloaded video (without extension)
    :return: Actual filename of the downloaded video
    """
    
    class FilesizeLimitError(Exception):
        pass

    def progress_hook(d):
        if d['status'] == 'finished':
            print("Download complete. Processing...")

    def filesize_limiter(info_dict, *args, **kwargs):
        filesize = info_dict.get('filesize', 0) or info_dict.get('filesize_approx', 0)
        if filesize and filesize > max_filesize_mb * 1024 * 1024:
            raise FilesizeLimitError("File size exceeds limit!")

    test = os.listdir("./")        
    for item in test:
        if item.startswith(suggested_filename):
            os.remove(os.path.join("./", item)) 

    actual_filename = None
    ydl_opts = {
        'format': 'best',
        'progress_hooks': [progress_hook],
        'outtmpl': f'{suggested_filename if suggested_filename else "%(title)s"}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'match_filter': filesize_limiter
    }
    
    actual_filename = recent_video_cache[url_hash]
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            url_hash = hash(url)
            if not actual_filename:
                result = ydl.extract_info(url, download=True)
                actual_filename = ydl.prepare_filename(f"result_{url_hash}")
                recent_video_cache[url_hash] = actual_filename #move this after exceptions?
    except FilesizeLimitError as e:
        print(f"Skipping download: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return actual_filename


