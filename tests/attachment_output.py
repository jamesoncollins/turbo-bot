import base64
import binascii
import re
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "test_output" / "attachments"
_send_counter = 0


def _safe_part(value):
    value = str(value or "unknown")
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value.strip("._")[:80] or "unknown"


def _extension_for_bytes(content):
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
        return ".gif"
    if b"ftyp" in content[:64]:
        return ".mp4"
    if content.startswith(b"%PDF"):
        return ".pdf"
    return ".bin"


def save_attachment_bytes(content, message=None, index=1):
    global _send_counter

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _send_counter += 1
    message_part = _safe_part(message)
    extension = _extension_for_bytes(content)
    output_path = OUTPUT_DIR / f"{_send_counter:04d}_{message_part}_{index:02d}{extension}"
    output_path.write_bytes(content)
    return output_path


def _decode_base64_attachment(attachment):
    if isinstance(attachment, str):
        attachment = attachment.strip()
        if "," in attachment and attachment.split(",", 1)[0].lower().endswith(";base64"):
            attachment = attachment.split(",", 1)[1]
        attachment = re.sub(r"\s+", "", attachment)
        attachment += "=" * (-len(attachment) % 4)

    return base64.b64decode(attachment, validate=True)


def save_base64_attachments(base64_attachments, message=None):
    global _send_counter

    if not base64_attachments:
        return []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _send_counter += 1
    message_part = _safe_part(message)
    written_files = []

    for index, attachment in enumerate(base64_attachments, start=1):
        try:
            content = _decode_base64_attachment(attachment)
            output_path = OUTPUT_DIR / f"{_send_counter:04d}_{message_part}_{index:02d}{_extension_for_bytes(content)}"
            output_path.write_bytes(content)
        except (binascii.Error, TypeError, ValueError):
            prefix = f"{_send_counter:04d}_{message_part}_{index:02d}"
            output_path = OUTPUT_DIR / f"{prefix}.b64.txt"
            output_path.write_text(str(attachment), encoding="utf-8")

        written_files.append(output_path)

    return written_files


def install_send_attachment_capture(send_mock_cls):
    if getattr(send_mock_cls, "_turbo_attachment_capture_installed", False):
        return

    original_execute_mock_call = send_mock_cls._execute_mock_call

    async def _execute_mock_call_with_attachment_capture(self, *args, **kwargs):
        save_base64_attachments(
            kwargs.get("base64_attachments"),
            message=args[1] if len(args) > 1 else kwargs.get("message"),
        )
        return await original_execute_mock_call(self, *args, **kwargs)

    send_mock_cls._execute_mock_call = _execute_mock_call_with_attachment_capture
    send_mock_cls._turbo_attachment_capture_installed = True
