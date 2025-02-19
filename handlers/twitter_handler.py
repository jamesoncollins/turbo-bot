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

    def can_handle(self) -> bool:
        url = self.extract_url(self.input_str)
        if not url:
            return False
        ydl = yt_dlp.YoutubeDL({'quiet': True})
        try:
            info = ydl.extract_info(url, download=False)
            return True
        except Exception:
            return False

    def process_message(self, msg, attachments):
        url = self.extract_url(self.input_str)
        video_content = download_video(url)
        if video_content:
            return {
                "message": "Downloaded video content using yt_dlp.",
                "attachments": [BaseHandler.file_to_base64(video_content)],
            }
        return []

    @staticmethod
    def get_name() -> str:
        return "yt_dlp Handler"
    
def download_video(url, max_filesize_mb=90, suggested_filename="downloaded_video.mp4"):
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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)            
            actual_filename = ydl.prepare_filename(result)
    except FilesizeLimitError as e:
        print(f"Skipping download: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        
    video_title = ""
    try:
        video_title = result["title"]
    except:
        pass
    print(f"Video title is: {video_title}")

    return actual_filename


