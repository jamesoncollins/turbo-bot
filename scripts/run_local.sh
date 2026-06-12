#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${ENV_NAME:-turbo-bot-wsl}"
SECRET_FILE="${REPO_ROOT}/secret.txt"
CONDA_STATE_DIR="${CONDA_STATE_DIR:-${REPO_ROOT}/.conda}"
CONDA_ENVS_PATH="${CONDA_ENVS_PATH:-${CONDA_STATE_DIR}/envs}"
CONDA_PKGS_DIRS="${CONDA_PKGS_DIRS:-${CONDA_STATE_DIR}/pkgs}"
ENV_PREFIX="${ENV_PREFIX:-${CONDA_ENVS_PATH}/${ENV_NAME}}"
XDG_CACHE_HOME="${XDG_CACHE_HOME:-${REPO_ROOT}/.cache}"

find_conda() {
    if command -v conda >/dev/null 2>&1; then
        command -v conda
        return 0
    fi

    local candidates=(
        "${SNAP_REAL_HOME:-}/miniforge3/bin/conda"
        "${SNAP_REAL_HOME:-}/Miniforge3/bin/conda"
        "${HOME}/miniforge3/bin/conda"
        "${HOME}/Miniforge3/bin/conda"
    )

    local candidate
    for candidate in "${candidates[@]}"; do
        if [[ -n "${candidate}" && -x "${candidate}" ]]; then
            echo "${candidate}"
            return 0
        fi
    done

    return 1
}

cd "${REPO_ROOT}"

if [[ ! -f "${SECRET_FILE}" ]]; then
    echo "Missing ${SECRET_FILE}. Create it from secret.example.txt before running locally." >&2
    exit 1
fi

set -a
source "${SECRET_FILE}"
set +a

required_vars=(
    SIGNAL_API_URL
    BOT_NUMBER
)

for var_name in "${required_vars[@]}"; do
    if [[ -z "${!var_name:-}" ]]; then
        echo "Required environment variable ${var_name} is not set in secret.txt." >&2
        exit 1
    fi
done

if [[ ! -d "${REPO_ROOT}/signalbot_local" ]] || [[ -z "$(find "${REPO_ROOT}/signalbot_local" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    echo "signalbot_local is missing. Run: git submodule update --init --recursive" >&2
    exit 1
fi

export CONDA_ENVS_PATH
export CONDA_PKGS_DIRS
export CONDA_NO_PLUGINS=true
export CONDA_SOLVER=classic
export PYTHONNOUSERSITE=1
export XDG_CACHE_HOME
mkdir -p "${XDG_CACHE_HOME}"

if CONDA_BIN="$(find_conda)"; then
    if [[ ! -d "${ENV_PREFIX}" ]]; then
        echo "Conda environment ${ENV_NAME} does not exist. Run scripts/bootstrap_wsl.sh first." >&2
        exit 1
    fi
    exec "${CONDA_BIN}" run --no-capture-output -p "${ENV_PREFIX}" python run.py
fi

exec python run.py
