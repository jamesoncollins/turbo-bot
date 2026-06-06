import unittest
from unittest.mock import patch

from handlers.base_handler import BaseHandler
from handlers.twitter_handler import TwitterHandler


class LinkHandlingTest(unittest.TestCase):
    def test_extract_url_strips_trailing_message_punctuation(self):
        self.assertEqual(
            BaseHandler.extract_url("check this https://x.com/user/status/12345)."),
            "https://x.com/user/status/12345",
        )

    def test_known_yt_dlp_domains_do_not_require_probe(self):
        with patch("handlers.twitter_handler.yt_dlp.YoutubeDL") as youtube_dl:
            handler = TwitterHandler("https://x.com/user/status/12345")
            self.assertTrue(handler.can_handle())
            youtube_dl.assert_not_called()

    def test_unknown_urls_still_fall_back_to_yt_dlp_probe(self):
        with patch("handlers.twitter_handler.yt_dlp.YoutubeDL") as youtube_dl:
            youtube_dl.return_value.extract_info.return_value = {}
            handler = TwitterHandler("https://example.com/video/12345")
            self.assertTrue(handler.can_handle())
            youtube_dl.return_value.extract_info.assert_called_once_with(
                "https://example.com/video/12345", download=False
            )


if __name__ == "__main__":
    unittest.main()
