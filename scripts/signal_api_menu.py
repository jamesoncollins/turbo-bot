#!/usr/bin/env python3
"""Interactive helper for common signal-cli-rest-api commands.

This script intentionally uses only the Python standard library so it can run in
any of this project's Docker containers that have Python installed.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 30


def normalize_base_url(value: str) -> str:
    value = value.strip().rstrip("/")
    if not value:
        return "http://localhost:8181"
    if "://" not in value:
        value = f"http://{value}"
    return value.rstrip("/")


def default_base_url() -> str:
    return normalize_base_url(
        os.environ.get("SIGNAL_API_BASE_URL")
        or os.environ.get("SIGNAL_API_URL")
        or "http://localhost:8181"
    )


def prompt(label: str, default: str | None = None, required: bool = False) -> str:
    suffix = f" [{default}]" if default not in (None, "") else ""
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if not value and default is not None:
            value = default
        if value or not required:
            return value
        print("This value is required.")


def prompt_bool(label: str, default: bool = False) -> bool:
    default_text = "Y/n" if default else "y/N"
    value = input(f"{label} [{default_text}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "true", "1"}


def split_recipients(value: str) -> list[str]:
    normalized = value.replace("\n", ";").replace(",", ";")
    return [part.strip() for part in normalized.split(";") if part.strip()]


def pretty_print(data: Any) -> None:
    if data is None:
        print("No response body.")
        return
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(data)


def request_api(
    base_url: str,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    query: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Any:
    if not path.startswith("/"):
        path = f"/{path}"
    url = f"{base_url}{path}"
    if query:
        clean_query = {key: value for key, value in query.items() if value != ""}
        if clean_query:
            url = f"{url}?{urllib.parse.urlencode(clean_query)}"

    encoded_body = None
    headers = {"Accept": "application/json"}
    if body is not None:
        encoded_body = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=encoded_body, headers=headers, method=method.upper())
    print(f"\n{method.upper()} {url}")
    if body is not None:
        print("Request body:")
        pretty_print(body)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            print(f"\nHTTP {response.status}")
            if not raw:
                return None
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        print(f"\nHTTP {exc.code}")
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        return None
    except urllib.error.URLError as exc:
        print(f"\nConnection failed: {exc}")
        print("Check the API base URL and whether the signal-cli REST container is reachable.")
        return None
    except TimeoutError:
        print("\nRequest timed out.")
        return None


def menu_accounts(base_url: str) -> None:
    pretty_print(request_api(base_url, "GET", "/v1/accounts"))


def menu_qr_link(base_url: str) -> None:
    device_name = prompt("Device name", "turbo-bot-local")
    path = "/v1/qrcodelink"
    url = f"{base_url}{path}?{urllib.parse.urlencode({'device_name': device_name})}"
    print("\nOpen this URL in a browser to display the QR code:")
    print(url)
    if prompt_bool("Fetch the endpoint now", False):
        pretty_print(request_api(base_url, "GET", path, query={"device_name": device_name}, timeout=5))


def menu_send(base_url: str) -> None:
    number = prompt("Sender Signal number", os.environ.get("BOT_NUMBER"), required=True)
    recipients = split_recipients(prompt("Recipients (comma, semicolon, or newline separated)", required=True))
    message = prompt("Message", required=True)
    payload: dict[str, Any] = {
        "number": number,
        "recipients": recipients,
        "message": message,
    }
    if prompt_bool("Add quote/reply metadata", False):
        payload["quote_author"] = prompt("Quote author")
        payload["quote_timestamp"] = prompt("Quote timestamp")
        payload["quote_message"] = prompt("Quote message")
    pretty_print(request_api(base_url, "POST", "/v2/send", payload))


def menu_receive(base_url: str) -> None:
    number = prompt("Signal number to receive for", os.environ.get("BOT_NUMBER"), required=True)
    timeout = prompt("Long-poll timeout seconds", "10")
    max_messages = prompt("Max messages", "10")
    ignore_attachments = "true" if prompt_bool("Ignore attachments", True) else "false"
    query = {
        "timeout": timeout,
        "max_messages": max_messages,
        "ignore_attachments": ignore_attachments,
    }
    path_number = urllib.parse.quote(number, safe="+")
    pretty_print(request_api(base_url, "GET", f"/v1/receive/{path_number}", query=query, timeout=int(timeout or "10") + 5))


def menu_groups(base_url: str) -> None:
    number = prompt("Signal number", os.environ.get("BOT_NUMBER"), required=True)
    path_number = urllib.parse.quote(number, safe="+")
    pretty_print(request_api(base_url, "GET", f"/v1/groups/{path_number}"))


def menu_raw(base_url: str) -> None:
    method = prompt("HTTP method", "GET").upper()
    path = prompt("API path, e.g. /v1/accounts", required=True)
    body = None
    if method in {"POST", "PUT", "PATCH", "DELETE"} and prompt_bool("Send JSON body", method == "POST"):
        raw_body = prompt("JSON body", "{}")
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON: {exc}")
            return
    pretty_print(request_api(base_url, method, path, body))


def choose_base_url(current: str) -> str:
    print("\nCommon values:")
    print("  - http://localhost:8181      (inside signal-cli container or host port mapping)")
    print("  - http://signal-cli:8181     (from another Docker Compose service)")
    print("  - $SIGNAL_API_URL / $SIGNAL_API_BASE_URL if set")
    return normalize_base_url(prompt("API base URL", current, required=True))


def run_menu(base_url: str) -> int:
    actions = {
        "1": ("List registered accounts", menu_accounts),
        "2": ("Show QR link URL", menu_qr_link),
        "3": ("Send a message", menu_send),
        "4": ("Receive messages", menu_receive),
        "5": ("List groups", menu_groups),
        "6": ("Raw API request", menu_raw),
    }

    while True:
        print("\nSignal REST API menu")
        print(f"Current API base URL: {base_url}")
        for key, (label, _callback) in actions.items():
            print(f"  {key}) {label}")
        print("  b) Change API base URL")
        print("  q) Quit")
        choice = input("Choose an option: ").strip().lower()

        if choice == "q":
            return 0
        if choice == "b":
            base_url = choose_base_url(base_url)
            continue
        action = actions.get(choice)
        if not action:
            print("Unknown option.")
            continue
        try:
            action[1](base_url)
        except KeyboardInterrupt:
            print("\nCancelled current action.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactive menu for common signal-cli-rest-api commands."
    )
    parser.add_argument(
        "--base-url",
        default=default_base_url(),
        help="Signal REST API base URL. Defaults to SIGNAL_API_BASE_URL, SIGNAL_API_URL, or http://localhost:8181.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    return run_menu(normalize_base_url(args.base_url))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
