# Operations

This guide describes the Docker-based deployment flow, Signal linking, and update behavior.

## Services

`docker-compose.yml` defines these services:

- `signal-cli`: runs `bbernhard/signal-cli-rest-api` in JSON-RPC mode.
- `signal-bot`: runs TurboBot from the configured main branch.
- `signal-bot-devel`: runs TurboBot from the configured development branch.
- `signal-bot-fs-editor`: optional filesystem editor/debug container that mounts bot volumes.

## Volumes

The compose file defines persistent volumes:

- `signal-cli-data`: Signal account/device state.
- `signal-bot-data`: repository data for the main bot container.
- `signal-bot-devel-data`: repository data for the development bot container.

## Bootstrap flow

The bot containers use a shell command in `docker-compose.yml` to:

1. Build `SETUP_SCRIPT_URL` from `GIT_REPO_URL`, `GIT_REPO_BRANCH`, and `SETUP_SCRIPT_NAME`.
2. Download `setup.sh` from that branch.
3. Mark it executable.
4. Run it.

`setup.sh` then:

1. Creates `GIT_REPO_PATH`.
2. Initializes the git repository if needed.
3. Configures the configured directory as a safe git directory.
4. Fetches from origin.
5. Resets hard to `origin/${GIT_REPO_BRANCH}`.
6. Initializes submodules.
7. Installs Python requirements.
8. Installs apt packages from `pkglist`.
9. Runs `run.sh`.

## Auto-update flow

`run.sh` launches `run.py` and monitors git for upstream changes.

The default loop:

1. Sleep for `CHECK_INTERVAL` seconds.
2. Run `git remote update`.
3. Compare local `@` with upstream `@{u}`.
4. If different, run `git pull`.
5. Kill the current Python process.
6. Relaunch `run.py`.

If `run.py` exits with a code other than `143`, `run.sh` sets an exit flag and exits.

## Operational warnings

- `setup.sh` runs `git reset --hard origin/${GIT_REPO_BRANCH}`. Local uncommitted edits inside the deployed repository can be discarded.
- `run.sh` sources `secret.txt` as shell code. Keep permissions tight and never commit real secrets.
- Media handlers may require `ffmpeg` and working network access.
- Some handlers depend on third-party services that can rate-limit, change HTML/API behavior, or require credentials.

## Linking Signal

On first setup, run `signal-cli` in normal mode and link it to a Signal account/device. With the REST API running locally, the QR-code link endpoint is typically:

```text
http://localhost:8181/v1/qrcodelink?device_name=local
```

Open that URL and scan the QR code with Signal on your phone. Keep the `signal-cli-data` volume so the linked device state persists.

## Manual signal-cli reference

The README contains an example `docker run` command generated from an existing `signal-cli` container. Use that only as a troubleshooting reference; the compose setup is the normal path.

If you need to regenerate that style of command from a running container, the original project notes used `docker inspect` and `jq` like this:

```bash
container_id="signal-cli"
docker inspect $container_id | jq -r '
  .[] |
  "docker run " +
  (if .Config.Env then (.Config.Env | map("--env \"" + . + "\"") | join(" ")) else "" end) + " " +
  (if .Config.Entrypoint then "--entrypoint \"" + (.Config.Entrypoint | join(" ")) + "\" " else "" end) +
  (if .Mounts then (.Mounts | map("--volume \"" + .Source + ":" + .Destination + "\"") | join(" ")) else "" end) + " " +
  (if .Config.Cmd then (.Config.Cmd | join(" ")) else "" end) +
  " " + .Config.Image
'
```
