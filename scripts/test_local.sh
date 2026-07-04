#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${ENV_NAME:-turbo-bot-wsl}"
CONDA_STATE_DIR="${CONDA_STATE_DIR:-${REPO_ROOT}/.conda}"
CONDA_ENVS_PATH="${CONDA_ENVS_PATH:-${CONDA_STATE_DIR}/envs}"
CONDA_PKGS_DIRS="${CONDA_PKGS_DIRS:-${CONDA_STATE_DIR}/pkgs}"
ENV_PREFIX="${ENV_PREFIX:-${CONDA_ENVS_PATH}/${ENV_NAME}}"
XDG_CACHE_HOME="${XDG_CACHE_HOME:-${REPO_ROOT}/.cache}"
TEST_OUTPUT=""

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

cleanup() {
    if [[ -n "${TEST_OUTPUT}" && -f "${TEST_OUTPUT}" ]]; then
        rm -f "${TEST_OUTPUT}"
    fi
}
trap cleanup EXIT

print_results_table() {
    local output_file="$1"

    awk '
        function record_result(result, test) {
            results[++count] = result
            tests[count] = test

            if (length(result) > max_result) {
                max_result = length(result)
            }
            if (length(test) > max_test) {
                max_test = length(test)
            }
        }

        function normalize_result(detail) {
            if (detail ~ /^skipped/) {
                return "SKIP"
            }
            if (detail ~ /^expected failure/) {
                return "XFAIL"
            }
            if (detail ~ /^unexpected success/) {
                return "XPASS"
            }
            if (detail ~ /^ok/) {
                return "PASS"
            }
            if (detail ~ /^FAIL/) {
                return "FAIL"
            }
            if (detail ~ /^ERROR/) {
                return "ERROR"
            }

            return ""
        }

        BEGIN {
            count = 0
            max_result = length("Result")
            max_test = length("Test")
            pending_test = ""
        }

        $0 ~ /^test[^[:space:]]+ \([^)]+\) \.\.\. / {
            split($0, parts, " ... ")
            test = parts[1]
            detail = parts[2]
            result = normalize_result(detail)

            if (result == "") {
                pending_test = test
            } else {
                record_result(result, test)
                pending_test = ""
            }
        }

        pending_test != "" && $0 ~ /^(ok|FAIL|ERROR|skipped|expected failure|unexpected success)( .*)?$/ {
            result = normalize_result($0)
            if (result != "") {
                record_result(result, pending_test)
                pending_test = ""
            }
        }

        END {
            if (count == 0) {
                print ""
                print "Test Results"
                print "No per-test results found. The test runner may have exited before discovery completed."
                exit
            }

            separator = "+"
            for (i = 0; i < max_result + 2; i++) {
                separator = separator "-"
            }
            separator = separator "+"
            for (i = 0; i < max_test + 2; i++) {
                separator = separator "-"
            }
            separator = separator "+"

            print ""
            print "Test Results"
            print separator
            printf "| %-" max_result "s | %-" max_test "s |\n", "Result", "Test"
            print separator
            for (i = 1; i <= count; i++) {
                printf "| %-" max_result "s | %-" max_test "s |\n", results[i], tests[i]
            }
            print separator
        }
    ' "${output_file}"
}

run_tests() {
    TEST_OUTPUT="$(mktemp)"

    set +e
    "$@" 2>&1 | tee "${TEST_OUTPUT}"
    local test_status=${PIPESTATUS[0]}
    set -e

    print_results_table "${TEST_OUTPUT}"
    return "${test_status}"
}

if [[ ! -d "${REPO_ROOT}/signalbot_local" ]] || [[ -z "$(find "${REPO_ROOT}/signalbot_local" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    echo "signalbot_local is missing. Run: git submodule update --init --recursive" >&2
    exit 1
fi

export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
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
    run_tests "${CONDA_BIN}" run -p "${ENV_PREFIX}" python -m unittest discover -v -s tests -p "test_*.py"
    exit $?
fi

run_tests python -m unittest discover -v -s tests -p "test_*.py"
