# handlers/twitter_handler.py
import yt_dlp
import os
import time
from handlers.base_handler import BaseHandler
from _ast import Try
from utils.misc_utils import *

class FilenameCollectorPP(yt_dlp.postprocessor.common.PostProcessor):
    def __init__(self):
        super(FilenameCollectorPP, self).__init__(None)
        self.filenames = []

    def run(self, information):
        self.filenames.append(information["filepath"])
        return [], information

STREAM_CLIP_SECONDS = 60


class TwitterHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._probe_url = None
        self._probe_info = None

    def _probe_download_info(self, url):
        if self._probe_url == url and self._probe_info is not None:
            return self._probe_info

        ydl = yt_dlp.YoutubeDL(_base_ydl_opts())
        info = ydl.extract_info(url, download=False)
        self._probe_url = url
        self._probe_info = info
        return info

    def can_handle(self) -> bool:
        url = self.extract_url(self.input_str)
        if not url:
            return False

        try:
            self._probe_download_info(url)
            return True
        except Exception:
            self._probe_url = None
            self._probe_info = None
            return False

    def process_message(self, msg, attachments):
        url = self.extract_url(self.input_str)
        info = self._probe_download_info(url)

        if _is_unavailable_stream(info):
            return {
                "message": "This looks like a stream, but it is not currently available to download.",
                "attachments": [],
            }

        is_stream = _is_live_stream(info)
        video_content = download_video(
            url,
            info=None if is_stream else info,
            stream_clip_seconds=STREAM_CLIP_SECONDS if is_stream else None,
        )
        if video_content:
            if is_stream:
                message = "Downloaded up to 1 minute from this stream using yt_dlp."
            else:
                message = "Downloaded video content using yt_dlp."
            return {
                "message": message,
                "attachments": [BaseHandler.file_to_base64(video_content)],
            }
        return []

    @staticmethod
    def get_name() -> str:
        return "yt_dlp Handler"


def _format_filesize_bytes(fmt):
    size = fmt.get("filesize")
    if size is None:
        size = fmt.get("filesize_approx")
    return int(size or 0)


def _pick_best_download_format(formats, max_filesize_mb):
    max_bytes = max_filesize_mb * 1024 * 1024

    best_muxed = None
    best_muxed_size = -1
    for fmt in formats:
        size = _format_filesize_bytes(fmt)
        has_video = fmt.get("vcodec") != "none"
        has_audio = fmt.get("acodec") != "none"
        if not (size and has_video and has_audio):
            continue
        if size <= max_bytes and size > best_muxed_size:
            best_muxed = fmt["format_id"]
            best_muxed_size = size

    if best_muxed:
        return best_muxed

    video_formats = []
    audio_formats = []
    for fmt in formats:
        size = _format_filesize_bytes(fmt)
        if not size:
            continue
        if fmt.get("vcodec") != "none" and fmt.get("acodec") == "none":
            video_formats.append(fmt)
        elif fmt.get("acodec") != "none" and fmt.get("vcodec") == "none":
            audio_formats.append(fmt)

    best_pair = None
    best_pair_size = -1
    for video_fmt in video_formats:
        if video_fmt.get("ext") != "mp4":
            continue
        for audio_fmt in audio_formats:
            if audio_fmt.get("ext") != "m4a":
                continue
            total_size = _format_filesize_bytes(video_fmt) + _format_filesize_bytes(audio_fmt)
            if total_size <= max_bytes and total_size > best_pair_size:
                best_pair = f'{video_fmt["format_id"]}+{audio_fmt["format_id"]}'
                best_pair_size = total_size

    return best_pair


def _live_status(info):
    return (info or {}).get("live_status")


def _is_live_stream(info):
    live_status = _live_status(info)
    return bool((info or {}).get("is_live")) or live_status == "is_live"


def _is_unavailable_stream(info):
    live_status = _live_status(info)
    return live_status in {"is_upcoming", "post_live"}


def _stream_tail_download_ranges(seconds):
    def download_ranges(info_dict, ydl):
        duration = info_dict.get("duration")
        if not duration:
            live_start = (
                info_dict.get("live_start_time")
                or info_dict.get("release_timestamp")
                or info_dict.get("timestamp")
            )
            if live_start:
                duration = max(time.time() - live_start, 0)

        if duration:
            end_time = max(float(duration), 0)
            start_time = max(end_time - seconds, 0)
        else:
            start_time = 0
            end_time = seconds

        yield {
            "start_time": start_time,
            "end_time": min(end_time, start_time + seconds),
            "title": f"Last {seconds} seconds of stream",
        }

    return download_ranges


def _base_ydl_opts():
    return {
        'quiet': True,
        'playlistend': 1,
        'js_runtimes': {'py_mini_racer': {}},
        'extractor_args': {'youtube': {'player_client': ['android', 'android_vr']}},
    }


def download_video(url, max_filesize_mb=90, suggested_filename="downloaded_video", info=None, stream_clip_seconds=None):
    """
    Downloads the best quality video below the specified file size limit.

    :param url: URL of the video to download
    :param max_filesize_mb: Maximum file size in megabytes
    :param suggested_filename: Suggested filename for the downloaded video (without extension)
    :return: Actual filename of the downloaded video
    """

    class FilesizeLimitError(Exception):
        pass

    ytdlp_max_filesize_bytes = int(1.25 * 1024 * 1024 * 1024)

    def progress_hook(d):
        if d['status'] == 'finished':
            print("Download complete. Processing...")

    def filesize_limiter(info_dict, *args, **kwargs):
        max_max_filesize_mb = 1500
        filesize = info_dict.get('filesize', 0) or info_dict.get('filesize_approx', 0)
        filesize = int(filesize)
        if filesize > max_max_filesize_mb * 1024 * 1024:
            raise FilesizeLimitError("File size exceeds limit!")

    # try and delete the filename we're gonna use
    test = os.listdir("./")
    for item in test:
        if item.startswith(suggested_filename):
            os.remove(os.path.join("./", item))


    # Get available formats
    base_ydl_opts = _base_ydl_opts()
    if stream_clip_seconds:
        base_ydl_opts['live_from_start'] = True
    if info is None:
        ydl = yt_dlp.YoutubeDL(base_ydl_opts)
        info = ydl.extract_info(url, download=False)

    formats = info.get("formats", [])
    selected_format = _pick_best_download_format(formats, max_filesize_mb)

    stream_range_opts = {}
    if stream_clip_seconds:
        stream_range_opts = {
            'download_ranges': _stream_tail_download_ranges(stream_clip_seconds),
            'force_keyframes_at_cuts': False,
            'live_from_start': True,
        }

    if selected_format:
        print(f"Found a format within size limit ({max_filesize_mb} MB). Downloading...")
        ydl_opts = {
            'format': selected_format,
            'progress_hooks': [progress_hook],
            'outtmpl': f'{suggested_filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'match_filter': filesize_limiter,
            'max_filesize': ytdlp_max_filesize_bytes,
            'playlistend': 1,                    # helps with twitter/dsky posts that have video in the comments
            'js_runtimes': base_ydl_opts['js_runtimes'],
            'extractor_args': base_ydl_opts['extractor_args'],
            **stream_range_opts,
        }
    else:
        print("No suitable format found. Downloading best quality and compressing if needed.")
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'progress_hooks': [progress_hook],
            'outtmpl': f'{suggested_filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'playlistend': 1,                    # helps with twitter/dsky posts that have video in the comments
            'js_runtimes': base_ydl_opts['js_runtimes'],
            'extractor_args': base_ydl_opts['extractor_args'],
            **stream_range_opts,
        }


    try:
        filename_collector = FilenameCollectorPP()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.add_post_processor(filename_collector)
            meta = ydl.extract_info(url, download=True)

            actual_filename = None
            if filename_collector.filenames:
                actual_filename = filename_collector.filenames[-1]
            elif meta.get("requested_downloads"):
                actual_filename = meta["requested_downloads"][-1].get("filepath")
            elif meta.get("filepath"):
                actual_filename = meta["filepath"]

            if not actual_filename:
                try:
                    ext = meta['ext']
                    actual_filename = f"{suggested_filename}.{ext}"
                except Exception:
                    try:
                        ext = meta['entries'][0]['ext']
                        actual_filename = f"{suggested_filename}.{ext}"
                    except Exception:
                        raise ValueError("cant get filename")
    except FilesizeLimitError as e:
        raise ValueError(f"error: {e}")
    except Exception as e:
        raise ValueError(f"error: {e}")

    print(f"Video file is: {actual_filename}")

    temp_input = actual_filename + ".in"
    os.rename(actual_filename, temp_input)
    output_fname = convert_to_mp4(temp_input, actual_filename, max_size_mb=max_filesize_mb, max_resolution=(2000, 2000))
    os.rename(output_fname, actual_filename)

    return actual_filename


