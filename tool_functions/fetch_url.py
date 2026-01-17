import re
from typing import Dict

import requests


def _html_to_text(html: str, max_chars: int = 120_000) -> str:
    html = html[:max_chars]
    html = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?>.*?</style>", " ", html)
    text = re.sub(r"(?is)<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_url(url: str, timeout_s: int = 15) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; turbo-bot/1.0)"}
    r = requests.get(url, headers=headers, timeout=timeout_s)
    r.raise_for_status()
    ctype = (r.headers.get("Content-Type") or "").lower()
    body = r.text if isinstance(r.text, str) else r.content.decode("utf-8", errors="replace")
    return _html_to_text(body) if "text/html" in ctype else body[:120_000]


TOOL_SPEC: Dict = {
    "type": "function",
    "name": "fetch_url",
    "function": {
        "name": "fetch_url",
        "description": "Fetch a URL and return extracted readable text (best-effort).",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "timeout_s": {"type": "integer"},
            },
            "required": ["url"],
        },
    },
}

TOOL_FN = fetch_url
