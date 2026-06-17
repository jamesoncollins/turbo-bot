# Local Development

Local development in WSL should use the same dependency files as deployment:

- `requirements.txt` for Python packages.
- `pkglist` for system packages.

Use Docker Compose for the deployed multi-container stack and real Signal device linking. Use the host-run workflow below for Codex work, local editing, and mocked tests.

## WSL quick start

1. Install Miniforge in WSL and ensure `conda` is on your shell `PATH`.
2. Clone the repo.
3. Bootstrap the local environment:

   ```bash
   git submodule update --init --recursive
   scripts/bootstrap_wsl.sh
   ```

4. Run tests:

   ```bash
   scripts/test_local.sh
   ```

## What bootstrap does

`scripts/bootstrap_wsl.sh`:

- Verifies the shell is running in WSL/Linux.
- Ensures the `signalbot_local/` submodule is checked out.
- Creates or updates the `turbo-bot-wsl` Conda environment.
- Installs packages from `pkglist`, preferring Conda packages for isolation and falling back to `apt` only when needed.
- Installs Python dependencies from `requirements.txt`.

This keeps local development aligned with the same package sources used by the deployed bot.

Always use the Conda-backed scripts for local work in this repo. The scripts set `PYTHONNOUSERSITE=1` so packages from `~/.local` cannot leak into the project environment; install or update Python packages with `scripts/bootstrap_wsl.sh` instead of using the system Python directly.

## Running the bot locally

Create `secret.txt` from the sample file:

```bash
cp secret.example.txt secret.txt
```

Then fill in at least:

```bash
export SIGNAL_API_URL="localhost:8181"
export BOT_NUMBER="+15555555555"
```

Start the bot with:

```bash
scripts/run_local.sh
```

Unlike `run.sh`, this local entrypoint does not poll GitHub or restart itself when the repo changes.

## Submodule requirement

`signalbot_local/` is a required submodule for local development and tests. If it is empty, run:

```bash
git submodule update --init --recursive
```

## Agent notes

- Preferred validation command: `scripts/test_local.sh`
- Preferred local bootstrap command: `scripts/bootstrap_wsl.sh`
- Secrets live in `secret.txt` and must not be committed.
- `setup.sh` and `run.sh` are deployment-oriented container scripts, not the recommended local workflow.
