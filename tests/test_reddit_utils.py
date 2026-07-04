import unittest
from unittest.mock import patch

from utils.reddit_utils import download_reddit_video, download_reddit_video_with_redvid


class RedditUtilsTest(unittest.TestCase):
    @patch("utils.reddit_utils.download_reddit_video_with_redvid")
    @patch("utils.reddit_utils.download_reddit_video_with_ytdlp")
    def test_download_reddit_video_prefers_ytdlp(self, ytdlp_mock, redvid_mock):
        ytdlp_mock.return_value = "reddit.mp4"

        self.assertEqual(
            download_reddit_video("https://www.reddit.com/r/videos/comments/6rrwyj/"),
            "reddit.mp4",
        )
        redvid_mock.assert_not_called()

    @patch("utils.reddit_utils.Downloader")
    def test_redvid_fallback_returns_local_absolute_path(self, downloader_cls):
        downloader = downloader_cls.return_value
        downloader.download.return_value = None

        with patch("utils.reddit_utils.os.remove"), \
                patch("utils.reddit_utils.os.path.abspath", return_value="/repo/reddit.mp4"):
            filename = download_reddit_video_with_redvid(
                "https://www.reddit.com/r/videos/comments/6rrwyj/",
                "reddit.mp4",
            )

        self.assertEqual(filename, "/repo/reddit.mp4")


if __name__ == "__main__":
    unittest.main()
