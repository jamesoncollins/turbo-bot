# handlers/twitter_handler.py
import yt_dlp
import os
from handlers.base_handler import BaseHandler
from _ast import Try

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
        ydl = yt_dlp.YoutubeDL({'quiet': True, 'playlistend': 1  })
        try:
            info = ydl.extract_info(url, download=False)
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
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
    
def download_video(url, max_filesize_mb=90, suggested_filename="downloaded_video"):
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
        'outtmpl': f'{suggested_filename}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'match_filter': filesize_limiter,
        'playlistend': 1                     # helps with twitter/dsky posts that have video in the comments
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url, download=True)            
           
            try:
                ext = meta['ext']
            except:
                pass
            
            try:
                ext = meta['entries'][0]['ext']
            except:
                raise "cant get filename"
            
    except FilesizeLimitError as e:
        raise ValueError(f"error: {e}")
    except Exception as e:
        raise ValueError(f"error: {e}")
        
    actual_filename = f"{suggested_filename}.{ext}"
    print(f"Video file is: {actual_filename}")

    return actual_filename


