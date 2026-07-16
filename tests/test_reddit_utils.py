import unittest
from unittest.mock import patch

from utils.reddit_utils import (
    download_reddit_video,
    download_reddit_video_tryall_b64,
    download_reddit_video_with_redvid,
    is_reddit_domain,
    normalize_reddit_url,
)


class RedditUtilsTest(unittest.TestCase):
    def test_is_reddit_domain_extracts_old_reddit_url(self):
        url = "https://old.reddit.com/r/WNBAgossips/comments/1ukm1y4/she_finally_had_enough/"

        self.assertEqual(
            is_reddit_domain(f"check this {url}"),
            "https://www.reddit.com/comments/1ukm1y4/",
        )

    def test_normalize_reddit_url_converts_host_and_comments_variants(self):
        variants = [
            "https://old.reddit.com/r/WNBAgossips/comments/1ukm1y4/she_finally_had_enough/",
            "https://new.reddit.com/r/WNBAgossips/comments/1ukm1y4/she_finally_had_enough/?share_id=abc",
            "https://www.reddit.com/r/WNBAgossips/comments/1ukm1y4/she_finally_had_enough/cmtid/",
            "https://reddit.com/comments/1ukm1y4/she_finally_had_enough/",
            "https://redd.it/1ukm1y4?utm_source=share",
        ]

        for url in variants:
            with self.subTest(url=url):
                self.assertEqual(
                    normalize_reddit_url(url),
                    "https://www.reddit.com/comments/1ukm1y4/",
                )

    def test_normalize_reddit_url_preserves_historical_reddit_test_urls(self):
        variants = [
            "https://www.reddit.com/r/videos/comments/6rrwyj/",
            "https://www.reddit.com/r/videos/comments/6rrwyj/that_small_heart_attack/",
            "https://www.reddit.com/r/videos/comments/6rrwyj/that_small_heart_attack/?utm_source=share",
        ]

        for url in variants:
            with self.subTest(url=url):
                self.assertEqual(
                    normalize_reddit_url(url),
                    "https://www.reddit.com/comments/6rrwyj/",
                )

    @patch("utils.reddit_utils.requests.get")
    def test_normalize_reddit_url_resolves_share_links(self, get_mock):
        response = get_mock.return_value
        response.url = "https://www.reddit.com/r/TikTokCringe/comments/abc123/title/?share_id=1"
        response.raise_for_status.return_value = None

        self.assertEqual(
            normalize_reddit_url("https://www.reddit.com/r/TikTokCringe/s/Z3w1KP6KAc"),
            "https://www.reddit.com/comments/abc123/",
        )
        get_mock.assert_called_once()

    def test_is_reddit_domain_strips_trailing_sentence_punctuation(self):
        self.assertEqual(
            is_reddit_domain("look https://redd.it/1ukm1y4."),
            "https://www.reddit.com/comments/1ukm1y4/",
        )

    @patch("utils.reddit_utils.download_reddit_video_with_redvid")
    @patch("utils.reddit_utils.download_reddit_video_with_ytdlp")
    def test_download_reddit_video_prefers_ytdlp(self, ytdlp_mock, redvid_mock):
        ytdlp_mock.return_value = "reddit.mp4"

        self.assertEqual(
            download_reddit_video("https://old.reddit.com/r/videos/comments/6rrwyj/title/"),
            "reddit.mp4",
        )
        ytdlp_mock.assert_called_once_with(
            "https://www.reddit.com/comments/6rrwyj/",
            "reddit.mp4",
        )
        redvid_mock.assert_not_called()

    @patch("utils.reddit_utils.download_reddit_video_with_redvid")
    @patch("utils.reddit_utils.download_reddit_video_with_ytdlp")
    def test_historical_reddit_urls_download_from_normalized_url(self, ytdlp_mock, redvid_mock):
        urls = [
            "https://www.reddit.com/r/videos/comments/6rrwyj/",
            "https://www.reddit.com/r/videos/comments/6rrwyj/that_small_heart_attack/",
            "https://www.reddit.com/r/videos/comments/6rrwyj/that_small_heart_attack/?utm_source=share",
        ]

        for url in urls:
            with self.subTest(url=url):
                ytdlp_mock.reset_mock()
                redvid_mock.reset_mock()
                ytdlp_mock.return_value = "reddit.mp4"

                self.assertEqual(download_reddit_video(url), "reddit.mp4")
                ytdlp_mock.assert_called_once_with(
                    "https://www.reddit.com/comments/6rrwyj/",
                    "reddit.mp4",
                )
                redvid_mock.assert_not_called()

    @patch("utils.reddit_utils.requests.get")
    @patch("utils.reddit_utils.download_reddit_video_with_redvid")
    @patch("utils.reddit_utils.download_reddit_video_with_ytdlp")
    def test_historical_reddit_share_url_downloads_from_normalized_url(
        self,
        ytdlp_mock,
        redvid_mock,
        get_mock,
    ):
        response = get_mock.return_value
        response.url = "https://www.reddit.com/r/TikTokCringe/comments/abc123/title/"
        response.raise_for_status.return_value = None
        ytdlp_mock.return_value = "reddit.mp4"

        self.assertEqual(
            download_reddit_video("https://www.reddit.com/r/TikTokCringe/s/Z3w1KP6KAc"),
            "reddit.mp4",
        )
        ytdlp_mock.assert_called_once_with(
            "https://www.reddit.com/comments/abc123/",
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

    @patch("utils.reddit_utils.Downloader")
    def test_redvid_fallback_handles_redvid_base_exception(self, downloader_cls):
        downloader = downloader_cls.return_value
        downloader.download.side_effect = BaseException("Incorrect URL format")

        with patch("utils.reddit_utils.os.remove"):
            self.assertIsNone(
                download_reddit_video_with_redvid(
                    "https://www.reddit.com/comments/6rrwyj/",
                    "reddit.mp4",
                )
            )

    @patch("utils.reddit_utils.get_video_as_base64", return_value=None)
    @patch("utils.reddit_utils.download_reddit_video", side_effect=Exception("yt-dlp failed"))
    def test_tryall_b64_handles_downloader_exception(self, download_mock, scrape_mock):
        self.assertIsNone(download_reddit_video_tryall_b64("https://redd.it/6rrwyj"))
        self.assertEqual(
            [call.args[0] for call in download_mock.call_args_list],
            ["https://www.reddit.com/comments/6rrwyj/", "https://redd.it/6rrwyj"],
        )
        self.assertEqual(
            [call.args[0] for call in scrape_mock.call_args_list],
            ["https://www.reddit.com/comments/6rrwyj/", "https://redd.it/6rrwyj"],
        )

    @patch("utils.reddit_utils.Downloader")
    def test_redvid_fallback_reraises_shutdown_exceptions(self, downloader_cls):
        downloader = downloader_cls.return_value
        downloader.download.side_effect = KeyboardInterrupt()

        with patch("utils.reddit_utils.os.remove"), self.assertRaises(KeyboardInterrupt):
            download_reddit_video_with_redvid(
                "https://www.reddit.com/comments/6rrwyj/",
                "reddit.mp4",
            )


if __name__ == "__main__":
    unittest.main()
