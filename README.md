# turbo-bot

TurboBot is a Python Signal bot that runs against the signal-cli REST API. It routes messages through dynamically discovered handlers in `handlers/`, supports hashtag commands such as `#gpt`, and can return text plus base64-encoded attachments.

## Documentation

- [Architecture](docs/ARCHITECTURE.md): runtime flow, dispatch, handler discovery, and important paths.
- [Configuration](docs/CONFIGURATION.md): required environment variables and `secret.txt` setup.
- [Operations](docs/OPERATIONS.md): Docker Compose services, bootstrap flow, auto-updates, and Signal linking.
- [Writing handlers](docs/HANDLERS.md): how to add new bot features.
- [GPT function tools](docs/GPT_TOOLS.md): how to add tools callable by the `#gpt` handler.
- [Testing](docs/TESTING.md): local test commands, mocks, and integration-test caveats.
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

Create a Python environment, install dependencies, and run tests:

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -p "test_*.py"
```

Some handlers require system packages, especially `ffmpeg`. Docker deployments install packages from `pkglist`.

## Manual signal-cli reference

If you need to reproduce a running `signal-cli` container manually, stop the existing instance first and adapt this example to your local volume paths:

```bash
docker run --env "MODE=json-rpc" --env "PORT=8181" --env "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" --env "GIN_MODE=release" --env "BUILD_VERSION=0.90" --env "SIGNAL_CLI_CONFIG_DIR=/home/.local/share/signal-cli" --env "SIGNAL_CLI_UID=1000" --env "SIGNAL_CLI_GID=1000" --entrypoint "/entrypoint.sh" --volume "/share/CACHEDEV1_DATA/Container/container-station-data/lib/docker/volumes/app-1_signal-cli-data/_data:/home/.local/share/signal-cli" bbernhard/signal-cli-rest-api:latest
```
