# README migration checklist

This checklist maps the original README content to the current documentation set so future reviewers can confirm that information was reorganized rather than dropped.

| Original README topic | Current location |
| --- | --- |
| Docker Compose runs the Signal bot and Signal REST API | `README.md` quick start; `docs/OPERATIONS.md` services section |
| Main and devel bot containers use different branches | `docs/OPERATIONS.md` services section |
| Bot containers monitor GitHub and download updates | `docs/OPERATIONS.md` auto-update flow |
| Required Signal API and bot number environment variables | `README.md` quick start; `docs/CONFIGURATION.md` required variables |
| Contact/group allow lists and ignored groups | `README.md` quick start; `docs/CONFIGURATION.md` message allow/ignore controls |
| Instagram and OpenAI environment variables | `docs/CONFIGURATION.md` optional feature credentials; `secret.example.txt` |
| Historical `secrets.txt`/`secrets.sh` wording | `docs/CONFIGURATION.md` notes the current launcher reads `secret.txt` |
| Updating `docker-compose.yml` to point at the desired repo/branches | `docs/CONFIGURATION.md` Docker Compose configuration; `docs/OPERATIONS.md` bootstrap flow |
| Linking Signal with the QR-code endpoint | `README.md` Signal linking; `docs/OPERATIONS.md` linking Signal |
| Manual `signal-cli` `docker run` example | `README.md` manual signal-cli reference |
| `docker inspect`/`jq` command used to generate the manual `docker run` command | `docs/OPERATIONS.md` manual signal-cli reference |
| Windows/Linux/WSL/macOS development note | `docs/TESTING.md` required dependencies |
| Miniconda recommendation for Windows | `docs/TESTING.md` required dependencies |
| Installing Python dependencies and running unittest discovery | `README.md` development; `docs/TESTING.md` basic command and dependencies |
| `ffmpeg` and other system package caveats | `README.md` development; `docs/TESTING.md` dependencies and troubleshooting |

## Secret-data review

The checked-in secret template intentionally contains only placeholders. Real local credentials should live in `secret.txt`, which remains ignored by `.gitignore` through the existing `*.txt` and `*secret*` patterns. The repository explicitly un-ignores only `secret.example.txt` so users have a safe template to copy.
