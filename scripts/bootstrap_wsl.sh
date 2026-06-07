#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${ENV_NAME:-turbo-bot-wsl}"
PYTHON_VERSION="${PYTHON_VERSION:-3.10}"
PKGLIST_FILE="${REPO_ROOT}/pkglist"
REQUIREMENTS_FILE="${REPO_ROOT}/requirements.txt"
SUBMODULE_PATH="${REPO_ROOT}/signalbot_local"
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

if [[ ! -f /proc/version ]] || ! grep -qi "microsoft\|wsl" /proc/version; then
    echo "This bootstrap script is intended for WSL/Linux environments." >&2
    exit 1
fi

if ! command -v git >/dev/null 2>&1; then
    echo "git is required but was not found." >&2
    exit 1
fi

if ! CONDA_BIN="$(find_conda)"; then
    echo "conda is required. Install Miniforge first, then re-run this script." >&2
    exit 1
fi

cd "${REPO_ROOT}"
mkdir -p "${CONDA_ENVS_PATH}" "${CONDA_PKGS_DIRS}"

export CONDA_ENVS_PATH
export CONDA_PKGS_DIRS
export CONDA_NO_PLUGINS=true
export CONDA_SOLVER=classic
export XDG_CACHE_HOME
mkdir -p "${XDG_CACHE_HOME}"

if [[ ! -f .gitmodules ]]; then
    echo "Expected .gitmodules to exist so signalbot_local can be managed as a submodule." >&2
    exit 1
fi

if [[ ! -d "${SUBMODULE_PATH}" ]] || [[ -z "$(find "${SUBMODULE_PATH}" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    echo "Initializing signalbot_local submodule..."
    git submodule update --init --recursive
fi

if [[ ! -f "${SUBMODULE_PATH}/setup.py" ]] && [[ ! -f "${SUBMODULE_PATH}/pyproject.toml" ]]; then
    echo "signalbot_local is still empty or incomplete after submodule init." >&2
    exit 1
fi

if [[ -d "${ENV_PREFIX}" ]]; then
    echo "Updating existing Conda environment: ${ENV_NAME}"
else
    echo "Creating Conda environment: ${ENV_NAME}"
    "${CONDA_BIN}" create -y -p "${ENV_PREFIX}" "python=${PYTHON_VERSION}" pip
fi

if [[ -f "${PKGLIST_FILE}" ]]; then
    mapfile -t packages < <(tr ' ' '\n' < "${PKGLIST_FILE}" | awk 'NF && $1 !~ /^#/')
else
    packages=()
fi

if [[ "${#packages[@]}" -gt 0 ]]; then
    conda_pkgs=()
    apt_pkgs=()

    for package in "${packages[@]}"; do
        if "${CONDA_BIN}" search -c conda-forge "${package}" >/dev/null 2>&1; then
            conda_pkgs+=("${package}")
        else
            apt_pkgs+=("${package}")
        fi
    done

    if [[ "${#conda_pkgs[@]}" -gt 0 ]]; then
        echo "Installing pkglist packages with Conda: ${conda_pkgs[*]}"
        "${CONDA_BIN}" install -y -p "${ENV_PREFIX}" -c conda-forge "${conda_pkgs[@]}"
    fi

    if [[ "${#apt_pkgs[@]}" -gt 0 ]]; then
        echo "Installing pkglist packages with apt: ${apt_pkgs[*]}"
        sudo apt-get update
        sudo apt-get install -y "${apt_pkgs[@]}"
    fi
fi

echo "Installing Python dependencies from requirements.txt"
"${CONDA_BIN}" run -p "${ENV_PREFIX}" python -m pip install --upgrade pip
"${CONDA_BIN}" run -p "${ENV_PREFIX}" python -m pip install -r "${REQUIREMENTS_FILE}"

echo
echo "Bootstrap complete."
echo "Activate the environment with:"
echo "  conda activate ${ENV_NAME}"
echo "Run tests with:"
echo "  scripts/test_local.sh"
echo "Run the bot locally with:"
echo "  scripts/run_local.sh"
