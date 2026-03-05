# handlers/twitter_handler.py
import hashlib
import os
import queue
import threading
from urllib.parse import urlparse, urlencode, parse_qsl
from typing import Callable

import yt_dlp

from handlers.base_handler import BaseHandler
from utils.misc_utils import convert_to_mp4


# ------------------------------------------------------------------ #
# Config                                                               #
# ------------------------------------------------------------------ #

CACHE_DIR        = os.path.join(os.path.dirname(__file__), "..", "cache", "twitter")
MAX_WORKERS      = 3
DOWNLOAD_TIMEOUT = 120  # seconds to wait before giving up

_work_queue: queue.Queue = queue.Queue()
_workers_started = False
_pool_lock        = threading.Lock()

_STRIP_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "si", "feature", "ref_src", "ref_url", "igshid", "s", "t",
}


# ------------------------------------------------------------------ #
# URL normalisation                                                    #
# ------------------------------------------------------------------ #

def _normalize_url(url: str) -> str:
    url = url.rstrip("$#&?. ")
    parsed = urlparse(url)
    clean_params = [
        (k, v) for k, v in parse_qsl(parsed.query)
        if k.lower() not in _STRIP_PARAMS
    ]
    return parsed._replace(query=urlencode(clean_params), fragment="").geturl()

def _url_hash(url: str) -> str:
    return hashlib.sha256(_normalize_url(url).encode()).hexdigest()

def _cached_path(url: str) -> str:
    return os.path.join(CACHE_DIR, f"{_url_hash(url)}.mp4")


# ------------------------------------------------------------------ #
# Worker pool                                                          #
# ------------------------------------------------------------------ #

def _ensure_workers():
    global _workers_started
    with _pool_lock:
        if not _workers_started:
            os.makedirs(CACHE_DIR, exist_ok=True)
            for _ in range(MAX_WORKERS):
                threading.Thread(target=_worker_loop, daemon=True).start()
            _workers_started = True

def _worker_loop():
    while True:
        url, result_queue = _work_queue.get()
        try:
            b64 = _fetch(url)
        except Exception as e:
            print(f"[TwitterHandler] Worker error for {url}: {e}")
            b64 = None
        finally:
            _work_queue.task_done()
        # Put result back into the per-request queue so the caller can pick it up
        result_queue.put(b64)


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
        url = self.extract_url(self.input_str)
        if not url:
            return {"message": "No URL found.", "attachments": []}

        _ensure_workers()

        # Each request gets its own result queue — the worker posts here when done
        result_queue: queue.Queue = queue.Queue()
        _work_queue.put((url, result_queue))

        print(f"[TwitterHandler] Waiting for download (timeout={DOWNLOAD_TIMEOUT}s)...")
        try:
            b64 = result_queue.get(timeout=DOWNLOAD_TIMEOUT)
        except queue.Empty:
            return {"message": "Download timed out. Try again or check the URL.", "attachments": []}

        if not b64:
            return {"message": "Failed to download video.", "attachments": []}

        return {
            "message": "Downloaded video content using yt_dlp.",
            "attachments": [b64],
        }

    @staticmethod
    def get_name() -> str:
        return "yt_dlp Handler"


# ------------------------------------------------------------------ #
# Cache + fetch                                                        #
# ------------------------------------------------------------------ #

def _fetch(url: str) -> str:
    cached = _cached_path(url)
    if os.path.exists(cached):
        print(f"[TwitterHandler] Cache hit: {cached}")
        return BaseHandler.file_to_base64(cached)

    norm = _normalize_url(url)
    print(f"[TwitterHandler] Cache miss, downloading: {norm}")
    download_video(norm, dest_path=cached)
    return BaseHandler.file_to_base64(cached)


# ------------------------------------------------------------------ #
# Download                                                             #
# ------------------------------------------------------------------ #

def download_video(url: str, dest_path: str, max_filesize_mb: int = 90) -> str:

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

    tmp_base = dest_path + ".tmp"

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

    ydl_opts = (
        {**shared_opts, "format": selected_format, "match_filter": filesize_limiter}
        if selected_format else
        {**shared_opts, "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"}
    )

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
    in_file  = raw_tmp + ".in"
    os.rename(raw_tmp, in_file)
    converted = convert_to_mp4(in_file, raw_tmp, max_size_mb=max_filesize_mb, max_resolution=(2000, 2000))

    # Atomic move — partial files never enter the cache
    os.rename(converted, dest_path)

    try:
        os.remove(in_file)
    except OSError:
        pass

    print(f"[TwitterHandler] Cached to: {dest_path}")
    return dest_path
