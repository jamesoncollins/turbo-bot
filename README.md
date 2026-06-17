# turbo-bot

TurboBot is a Python Signal bot that runs against the signal-cli REST API. It routes messages through dynamically discovered handlers in `handlers/`, supports hashtag commands such as `#gpt`, and can return text plus base64-encoded attachments.

## Documentation

- [Architecture](docs/ARCHITECTURE.md): runtime flow, dispatch, handler discovery, and important paths.
- [Configuration](docs/CONFIGURATION.md): required environment variables and `secret.txt` setup.
- [Local Development](docs/LOCAL_DEVELOPMENT.md): WSL/Codex bootstrap, local run, and mocked test workflow.
- [Operations](docs/OPERATIONS.md): Docker Compose services, bootstrap flow, auto-updates, and Signal linking.
- [Writing handlers](docs/HANDLERS.md): how to add new bot features.
- [GPT function tools](docs/GPT_TOOLS.md): how to add tools callable by the `#gpt` handler.
- [Testing](docs/TESTING.md): local test commands, mocks, and integration-test caveats.
- [Signal API menu](docs/SIGNAL_API_MENU.md): interactive helper for common signal-cli REST API commands.
- [README migration checklist](docs/README_MIGRATION.md): where the original README content moved and why no setup guidance was dropped.

## Quick start

1. Start the Docker Compose stack.
2. Link `signal-cli` to a Signal account/device if this is the first run.
3. Copy the sample secret file and edit it with real values:

   ```bash
   cp secret.example.txt secret.txt
   ```

4. Configure at least:

   ```bash
   export SIGNAL_API_URL="signal-cli:8181"
   export BOT_NUMBER="+15555555555"
   export CONTACT_NUMBERS="+15555555555"
   export GROUP_NAMES="My Signal Group"
   ```

See [Configuration](docs/CONFIGURATION.md) for all supported variables.

## Signal linking

When you first run this, start signal-cli and link it to your account by scanning a QR code with your phone. With the REST API exposed locally, the QR-code endpoint is typically:

```text
http://localhost:8181/v1/qrcodelink?device_name=local
```

See [Operations](docs/OPERATIONS.md) for more deployment details.

## Development

For WSL/Codex local development, use the checked-in bootstrap scripts so the host environment is built from the same files the containers use:

```bash
git submodule update --init --recursive
scripts/bootstrap_wsl.sh
scripts/test_local.sh
```

This workflow uses:

- `requirements.txt` for Python dependencies
- `pkglist` for system packages

See [Local Development](docs/LOCAL_DEVELOPMENT.md) for the full WSL workflow and [Testing](docs/TESTING.md) for test notes.

Some handlers require system packages, especially `ffmpeg`. Docker deployments install packages from `pkglist`, and the WSL bootstrap script installs from the same file.

## Manual signal-cli reference

If you need to reproduce a running `signal-cli` container manually, stop the existing instance first and adapt this example to your local volume paths:

```bash
docker run --env "MODE=json-rpc" --env "PORT=8181" --env "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" --env "GIN_MODE=release" --env "BUILD_VERSION=0.90" --env "SIGNAL_CLI_CONFIG_DIR=/home/.local/share/signal-cli" --env "SIGNAL_CLI_UID=1000" --env "SIGNAL_CLI_GID=1000" --entrypoint "/entrypoint.sh" --volume "/share/CACHEDEV1_DATA/Container/container-station-data/lib/docker/volumes/app-1_signal-cli-data/_data:/home/.local/share/signal-cli" bbernhard/signal-cli-rest-api:latest
```
