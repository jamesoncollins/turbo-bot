import unittest
from handlers.base_handler import BaseHandler

class TestURLs(unittest.TestCase):  # Inherit from unittest.TestCase

    def test_urls(self):  # Remove 'async', unittest does not support it
        
        urls = [
            "http://example.com/path",
            "https://example.com",
            "http://www.example.com",
            "https://www.example.com/another/path",
            "http://subdomain.example.com",
            "ftp://example.com",
            "example.com/path"
        ]
        target_domains = ["example.com", "examp.le"]

        for url in urls:
            if BaseHandler.is_url_in_domains(url, target_domains):
                self.assertTrue(True)  # Replace print with an assertion
            else:
                self.assertTrue(False, f"URL '{url}' should belong to '{target_domains}' but doesn't.")

            
if __name__ == "__main__":
    unittest.main()