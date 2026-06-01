# Testing

TurboBot uses Python `unittest` tests under `tests/`.

## Basic command

Run all tests with:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Test infrastructure

`tests/TurboTestCase.py` provides the shared bot test harness. Individual tests patch Signal API calls with mocks from `signalbot.utils`, especially:

- `ReceiveMessagesMock`
- `SendMessagesMock`

This allows tests to feed synthetic Signal messages into the bot and inspect outgoing replies without talking to a real Signal server.

## Local deterministic tests

Prefer adding tests that:

- Avoid real network access.
- Mock external APIs.
- Mock file downloads and media conversion.
- Assert on send count, message text, and attachment count.

`tests/test_run.py` and `tests/test_mmw.py` contain examples of command-level assertions.

## Network or integration-sensitive tests

Some existing tests and handlers may involve live external services or external binaries, including:

- Reddit downloads.
- YouTube, TikTok, X/Twitter, and Bluesky media downloads.
- NASA/JPL asteroid API requests.
- OpenAI model calls.
- Instagram login/download behavior.
- Finance/ticker data through `yfinance`.

These can fail because of network outages, API changes, rate limits, missing credentials, or missing system dependencies. When adding new tests for these areas, prefer mocking the service boundary unless the test is explicitly intended as an integration test.

## Required dependencies

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Development should work on Windows, Linux, WSL, and macOS. On Windows, the original project notes recommend Miniconda: create a new environment, install Python 3, and then run `pip3 install -r requirements.txt`.

Some handlers also require apt/system packages from `pkglist`, especially media tooling such as `ffmpeg`. If you are developing outside Docker, install `ffmpeg` through your platform package manager, Conda, WSL, or similar.

## Troubleshooting

### Missing `signalbot_local/`

`run.py` and tests try to add `signalbot_local/` to `sys.path` if present. This is optional in many environments, but useful when testing a local copy of the `signalbot` package.

### Missing environment variables

Some paths expect variables such as `SIGNAL_API_URL`, `BOT_NUMBER`, `CONTACT_NUMBERS`, `GROUP_NAMES`, or `OPENAI_API_KEY`. Tests often mock around these, but local manual runs need a configured `secret.txt`.

### Missing external binaries

Video download or conversion paths may require `ffmpeg`. Install packages from `pkglist` or use the Docker environment.

### Network failures and rate limits

Handlers that scrape or call third-party services may fail even if the code is correct. Re-run after confirming network access, credentials, and service availability.
