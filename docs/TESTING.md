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

For WSL/local development, bootstrap from the repo scripts:

```bash
git submodule update --init --recursive
scripts/bootstrap_wsl.sh
```

This installs the same dependency sources used by deployment:

- Python packages from `requirements.txt`
- System packages from `pkglist`

The recommended local workflow is WSL with Miniforge. `scripts/bootstrap_wsl.sh` prefers Conda packages for isolation and falls back to `apt` when a package from `pkglist` is not practical to install through Conda.

Some handlers also require system tools such as `ffmpeg`. The bootstrap script installs these from `pkglist`.

## Troubleshooting

### Missing `signalbot_local/`

`signalbot_local/` is a required submodule for this repo's local development flow. If it is empty, run `git submodule update --init --recursive`.

### Missing environment variables

Some paths expect variables such as `SIGNAL_API_URL`, `BOT_NUMBER`, `CONTACT_NUMBERS`, `GROUP_NAMES`, or `OPENAI_API_KEY`. Tests often mock around these, but local manual runs need a configured `secret.txt`.

### Missing external binaries

Video download or conversion paths may require `ffmpeg`. Install packages from `pkglist` or use the Docker environment.

### Network failures and rate limits

Handlers that scrape or call third-party services may fail even if the code is correct. Re-run after confirming network access, credentials, and service availability.
