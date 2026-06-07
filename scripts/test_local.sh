#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${ENV_NAME:-turbo-bot-wsl}"
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

if [[ ! -d "${REPO_ROOT}/signalbot_local" ]] || [[ -z "$(find "${REPO_ROOT}/signalbot_local" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    echo "signalbot_local is missing. Run: git submodule update --init --recursive" >&2
    exit 1
fi

export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
export CONDA_ENVS_PATH
export CONDA_PKGS_DIRS
export CONDA_NO_PLUGINS=true
export CONDA_SOLVER=classic
export XDG_CACHE_HOME
mkdir -p "${XDG_CACHE_HOME}"

if CONDA_BIN="$(find_conda)"; then
    if [[ ! -d "${ENV_PREFIX}" ]]; then
        echo "Conda environment ${ENV_NAME} does not exist. Run scripts/bootstrap_wsl.sh first." >&2
        exit 1
    fi
    "${CONDA_BIN}" run -p "${ENV_PREFIX}" python -m unittest discover -s tests -p "test_*.py"
    exit $?
fi

python -m unittest discover -s tests -p "test_*.py"
