import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import attachment_output


class AttachmentOutputTest(unittest.TestCase):
    def test_save_base64_attachments_decodes_files(self):
        mp4_like_content = b"\x00\x00\x00\x18ftypmp42" + b"video-bytes"
        attachment = base64.b64encode(mp4_like_content).decode("ascii")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(attachment_output, "OUTPUT_DIR", Path(tmpdir)):
                written_files = attachment_output.save_base64_attachments(
                    [attachment],
                    message="https://example.com/video",
                )

            self.assertEqual(len(written_files), 1)
            self.assertEqual(written_files[0].suffix, ".mp4")
            self.assertEqual(written_files[0].read_bytes(), mp4_like_content)

    def test_save_base64_attachments_handles_data_urls_and_padding(self):
        png_like_content = b"\x89PNG\r\n\x1a\n" + b"image-bytes"
        attachment = base64.b64encode(png_like_content).decode("ascii").rstrip("=")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(attachment_output, "OUTPUT_DIR", Path(tmpdir)):
                written_files = attachment_output.save_base64_attachments(
                    [f"data:image/png;base64,\n{attachment}\n"],
                    message="chart",
                )

            self.assertEqual(len(written_files), 1)
            self.assertEqual(written_files[0].suffix, ".png")
            self.assertEqual(written_files[0].read_bytes(), png_like_content)

    def test_save_attachment_bytes_uses_real_file_type(self):
        mp4_like_content = b"\x00\x00\x00\x18ftypmp42" + b"video-bytes"

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(attachment_output, "OUTPUT_DIR", Path(tmpdir)):
                output_path = attachment_output.save_attachment_bytes(
                    mp4_like_content,
                    message="live-download",
                )

            self.assertEqual(output_path.suffix, ".mp4")
            self.assertEqual(output_path.read_bytes(), mp4_like_content)


if __name__ == "__main__":
    unittest.main()
