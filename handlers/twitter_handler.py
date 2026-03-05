# handlers/twitter_handler.py
import hashlib
import os
import queue
import threading
from typing import Callable

import yt_dlp

from handlers.base_handler import BaseHandler
from utils.misc_utils import convert_to_mp4


# ------------------------------------------------------------------ #
# Module-level worker pool — shared across all handler instances       #
# ------------------------------------------------------------------ #

CACHE_DIR        = os.path.join(os.path.dirname(__file__), "..", "cache", "twitter")
MAX_WORKERS      = 3          # concurrent downloads
_work_queue      = queue.Queue()
_workers_started = False
_pool_lock       = threading.Lock()

def _ensure_workers():
    """Lazily start the worker pool once, the first time a job is queued."""
    global _workers_started
    with _pool_lock:
        if not _workers_started:
            os.makedirs(CACHE_DIR, exist_ok=True)
            for _ in range(MAX_WORKERS):
                t = threading.Thread(target=_worker_loop, daemon=True)
                t.start()
            _workers_started = True

def _worker_loop():
    """Each worker pulls jobs from the shared queue until the process exits."""
    while True:
        url, callback = _work_queue.get()
        try:
            b64 = _fetch(url)
        except Exception as e:
            print(f"[TwitterHandler] Worker error for {url}: {e}")
            b64 = None
        finally:
            _work_queue.task_done()
        callback(b64)

def _enqueue(url: str, callback: Callable[[str | None], None]):
    _ensure_workers()
    print(f"[TwitterHandler] Queued (queue depth: {_work_queue.qsize() + 1}): {url}")
    _work_queue.put((url, callback))


# ------------------------------------------------------------------ #
# Handler                                                              #
# ------------------------------------------------------------------ #

class TwitterHandler(BaseHandler):

    def can_handle(self) -> bool:
        url = self.extract_url(self.input_str)
        if not url:
            return False
        with yt_dlp.YoutubeDL({"quiet": True, "playlistend": 1}) as ydl:
            try:
                ydl.extract_info(url, download=False)
                return True
            except Exception as e:
                print(f"[TwitterHandler] can_handle probe failed: {e}")
                return False

    def process_message(self, msg, attachments):
        """
        Returns immediately. The download (or cache hit) is handled by the
        worker pool and the result delivered via _on_complete.
        """
        url = self.extract_url(self.input_str)
        if not url:
            return {"message": "No URL found.", "attachments": []}

        _enqueue(url, self._on_complete)
        return {"message": "Downloading video, please wait...", "attachments": []}

    def _on_complete(self, b64: str | None):
        """
        Called by a worker thread when the job finishes.
        Wire into your bot/message dispatch here.
        """
        if not b64:
            print("[TwitterHandler] Job produced no output.")
            return
        print(f"[TwitterHandler] Ready — {len(b64)} b64 chars.")
        # TODO: dispatch to user, e.g.:
        # self.reply({"message": "Here's your video.", "attachments": [b64]})

    @staticmethod
    def get_name() -> str:
        return "yt_dlp Handler"


# ------------------------------------------------------------------ #
# Cache + fetch                                                        #
# ------------------------------------------------------------------ #

def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()

def _cached_path(url: str) -> str:
    return os.path.join(CACHE_DIR, f"{_url_hash(url)}.mp4")

def _fetch(url: str) -> str:
    """
    Returns base64 of the video for url.
    Hits the on-disk cache if available, otherwise downloads.
    Thread-safe: each URL gets its own filename so workers never collide.
    """
    cached = _cached_path(url)
    if os.path.exists(cached):
        print(f"[TwitterHandler] Cache hit: {cached}")
        return BaseHandler.file_to_base64(cached)

    print(f"[TwitterHandler] Cache miss, downloading: {url}")
    filepath = download_video(url, dest_path=cached)
    return BaseHandler.file_to_base64(filepath)


# ------------------------------------------------------------------ #
# Download                                                             #
# ------------------------------------------------------------------ #

def download_video(url: str, dest_path: str, max_filesize_mb: int = 90) -> str:
    """
    Downloads url and saves the final mp4 to dest_path.
    Returns dest_path on success, raises ValueError on failure.
    """

    class FilesizeLimitError(Exception):
        pass

    def progress_hook(d):
        if d["status"] == "finished":
            print("[yt_dlp] Download complete, post-processing...")

    def filesize_limiter(info_dict, *args, **kwargs):
        filesize = int(info_dict.get("filesize", 0) or info_dict.get("filesize_approx", 0))
        if filesize > 1500 * 1024 * 1024:
            raise FilesizeLimitError("Exceeds 1.5 GB hard cap")

    base_opts = {
        "quiet": True,
        "playlistend": 1,
        "js_runtimes": {"py_mini_racer": {}},
        "extractor_args": {"youtube": {"player_client": ["android"]}},
    }

    # Use a temp path alongside dest_path so partial downloads never
    # land in the cache as if they were valid completed files
    tmp_base = dest_path + ".tmp"

    # Probe formats
    with yt_dlp.YoutubeDL(base_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    selected_format = None
    max_seen = 0
    for fmt in info.get("formats", []):
        filesize = fmt.get("filesize", 0)
        has_video = fmt.get("vcodec") != "none"
        has_audio = fmt.get("acodec") != "none"
        if filesize and has_video and has_audio and filesize <= max_filesize_mb * 1024 * 1024:
            if filesize > max_seen:
                max_seen = filesize
                selected_format = fmt["format_id"]

    shared_opts = {
        "progress_hooks": [progress_hook],
        "outtmpl": f"{tmp_base}.%(ext)s",
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        "playlistend": 1,
        **base_opts,
    }

    if selected_format:
        ydl_opts = {**shared_opts, "format": selected_format, "match_filter": filesize_limiter}
    else:
        ydl_opts = {
            **shared_opts,
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url, download=True)
            try:
                ext = meta["ext"]
            except (KeyError, TypeError):
                try:
                    ext = meta["entries"][0]["ext"]
                except Exception:
                    raise ValueError("Could not determine extension from yt_dlp metadata")
    except FilesizeLimitError as e:
        raise ValueError(f"File too large: {e}")
    except Exception as e:
        raise ValueError(f"yt_dlp error: {e}")

    raw_tmp = f"{tmp_base}.{ext}"

    # convert_to_mp4 handles compression/resize via your existing util
    in_file = raw_tmp + ".in"
    os.rename(raw_tmp, in_file)
    converted = convert_to_mp4(in_file, raw_tmp, max_size_mb=max_filesize_mb, max_resolution=(2000, 2000))

    # Atomic move into the cache slot — only appears as valid once complete
    os.rename(converted, dest_path)

    try:
        os.remove(in_file)
    except OSError:
        pass

    print(f"[TwitterHandler] Cached to: {dest_path}")
    return dest_path
