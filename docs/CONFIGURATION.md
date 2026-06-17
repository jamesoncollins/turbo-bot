# Configuration

TurboBot is configured mostly through environment variables loaded by `run.sh` before `run.py` starts.

## Secret file

`run.sh` currently looks for a file named `secret.txt` in the repository root and sources it as shell code.

Create a local `secret.txt` from the checked-in template:

```bash
cp secret.example.txt secret.txt
```

Then edit `secret.txt` with real values. Do not commit real secrets.

Older project notes referred to `secrets.txt` or `secrets.sh`; the current launcher reads `secret.txt`.

## Environment variables

### Required for normal operation

```bash
export SIGNAL_API_URL="signal-cli:8181"
export BOT_NUMBER="+15555555555"
```

- `SIGNAL_API_URL`: URL or host:port for the signal-cli REST API.
- `BOT_NUMBER`: registered Signal phone number for the bot.

### Message allow/ignore controls

```bash
export CONTACT_NUMBERS="+15555555555;+15555555556"
export GROUP_NAMES="My Signal Group;Another Signal Group"
export IGNORE_GROUPS="TurboBot Devel"
```

- `CONTACT_NUMBERS`: private contacts allowed to use the bot.
- `GROUP_NAMES`: Signal groups allowed to use the bot.
- `IGNORE_GROUPS`: optional group names to ignore even if otherwise allowed.

`CONTACT_NUMBERS`, `GROUP_NAMES`, and `IGNORE_GROUPS` are parsed by `utils.misc_utils.parse_env_var`:

- unset or empty values become `None`.
- exact lowercase `true` and `false` become booleans.
- semicolon-separated values become lists.
- a single non-empty value becomes a one-item list.

### Optional feature credentials

```bash
export OPENAI_API_KEY="replace-with-your-openai-api-key"
export INSTA_USERNAME="myuser"
export INSTA_PASSWORD="replace-with-your-instagram-password"
```

- `OPENAI_API_KEY`: enables the `#gpt` handler and OpenAI model/tool calls.
- `INSTA_USERNAME` and `INSTA_PASSWORD`: used by Instagram-related functionality when enabled.

## Docker Compose configuration

`docker-compose.yml` also sets deployment variables for the bot containers:

- `GIT_REPO_URL`: repository to clone/fetch.
- `GIT_REPO_PATH`: path inside the container where the repository is stored.
- `GIT_REPO_BRANCH`: branch to check out, reset to `origin/<branch>`, and run.
- `SETUP_SCRIPT_NAME`: bootstrap script name, normally `setup.sh`.

See `docs/OPERATIONS.md` for the full container startup flow.
