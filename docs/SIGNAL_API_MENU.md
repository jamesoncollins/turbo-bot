# Signal REST API interactive menu

`scripts/signal_api_menu.py` is a small, interactive wrapper around common
[`signal-cli-rest-api`](https://bbernhard.github.io/signal-cli-rest-api/) calls.
It is meant for the same situations where you would normally run `curl`, but
with prompts for the sender number, recipients, messages, and common lookup
commands.

The script uses only the Python standard library, so it does not require the
project's Python dependencies to be installed.

## Start the menu

From a TurboBot checkout inside a project container or on the Docker host:

```bash
scripts/signal_api_menu.py
```

If the script cannot find the Signal REST API, pass the base URL explicitly:

```bash
scripts/signal_api_menu.py --base-url http://signal-cli:8181
```

Useful base URLs are:

- `http://localhost:8181` when running in the `signal-cli` container or from a
  host with the Compose port mapping available.
- `http://signal-cli:8181` when running from another service on the same Docker
  Compose network.
- `SIGNAL_API_BASE_URL` or `SIGNAL_API_URL` when either environment variable is
  already set.

## Menu commands

The menu currently wraps these common API calls:

- `GET /v1/accounts` to list registered accounts.
- `GET /v1/qrcodelink?device_name=...` to build or fetch a QR-code link.
- `POST /v2/send` to send a Signal message.
- `GET /v1/receive/{number}` to receive messages for a linked number.
- `GET /v1/groups/{number}` to list groups for a linked number.
- A raw request mode for less common endpoints.

For send operations, recipients can be entered as a comma-separated,
semicolon-separated, or newline-separated list.
