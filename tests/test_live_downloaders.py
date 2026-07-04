import base64
import glob
import os
import unittest

from handlers.twitter_handler import download_video
from utils.reddit_utils import download_reddit_video_tryall_b64


LIVE_DOWNLOAD_URLS = {
    "bsky": "https://bsky.app/profile/bubbaprog.lol/post/3lga5ktfrx22o",
    "instagram_reel": "https://www.instagram.com/reel/DZuD9sTMeZU/",
    "reddit": "https://www.reddit.com/r/videos/comments/6rrwyj/that_small_heart_attack/",
    "tiktok": "https://tiktok.com/@underrated.simpsons/video/7410898661741251873",
    "x": "https://x.com/SaveUSAKitty/status/1872667773484363883",
    "youtube": "https://www.youtube.com/watch?v=hj4TXUJadt4",
    "youtube_short": "https://www.youtube.com/shorts/hw3pZaVL9YQ",
}


@unittest.skipUnless(
    os.environ.get("RUN_LIVE_DOWNLOAD_TESTS") == "1",
    "set RUN_LIVE_DOWNLOAD_TESTS=1 to run live downloader integration tests",
)
class LiveDownloaderTest(unittest.TestCase):
    def tearDown(self):
        for pattern in ("live_download_*", "reddit*"):
            for filename in glob.glob(pattern):
                try:
                    os.remove(filename)
                except FileNotFoundError:
                    pass

    def assert_downloaded_video_file(self, filename):
        self.assertTrue(os.path.exists(filename))
        self.assertGreater(os.path.getsize(filename), 1024)

        with open(filename, "rb") as video_file:
            header = video_file.read(64)
        self.assertIn(b"ftyp", header)

    def assert_ytdlp_downloads_video(self, url, suggested_filename):
        filename = download_video(
            url,
            max_filesize_mb=90,
            suggested_filename=suggested_filename,
        )

        self.assert_downloaded_video_file(filename)

    def test_reddit_video_download_returns_valid_video_base64(self):
        video_b64 = download_reddit_video_tryall_b64(LIVE_DOWNLOAD_URLS["reddit"])

        self.assertIsNotNone(video_b64)
        decoded = base64.b64decode(video_b64, validate=True)

        self.assertGreater(len(decoded), 1024)
        self.assertIn(b"ftyp", decoded[:64])

    def test_bsky_video_download_returns_video_file(self):
        self.assert_ytdlp_downloads_video(
            LIVE_DOWNLOAD_URLS["bsky"],
            "live_download_bsky",
        )

    def test_instagram_reel_download_returns_video_file(self):
        self.assert_ytdlp_downloads_video(
            LIVE_DOWNLOAD_URLS["instagram_reel"],
            "live_download_instagram_reel",
        )

    def test_tiktok_video_download_returns_video_file(self):
        self.assert_ytdlp_downloads_video(
            LIVE_DOWNLOAD_URLS["tiktok"],
            "live_download_tiktok",
        )

    def test_x_video_download_returns_video_file(self):
        self.assert_ytdlp_downloads_video(
            LIVE_DOWNLOAD_URLS["x"],
            "live_download_x",
        )

    def test_youtube_video_download_returns_video_file(self):
        self.assert_ytdlp_downloads_video(
            LIVE_DOWNLOAD_URLS["youtube"],
            "live_download_youtube",
        )

    def test_youtube_short_download_returns_video_file(self):
        self.assert_ytdlp_downloads_video(
            LIVE_DOWNLOAD_URLS["youtube_short"],
            "live_download_youtube_short",
        )


if __name__ == "__main__":
    unittest.main()
