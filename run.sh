#!/bin/bash

# Define variables
PYTHON_SCRIPT="run.py"   # Replace with the name of your Python script
CHECK_INTERVAL=10                # Time interval to check the repo for updates (in seconds)
EXIT_FLAG_FILE="/tmp/exit_flag"  # File used to indicate when the script should exit
PYTHON_PID_FILE="/tmp/python_pid" # File used to store the Python script's PID
BRANCH_REQUEST_FILE="${BRANCH_REQUEST_FILE:-/tmp/git_branch_request}"
BRANCH_SWITCH_EXIT_CODE="${BRANCH_SWITCH_EXIT_CODE:-42}"
export PYTHONPATH=$(pwd)/signalbot_local/

# Ensure no leftover flag or PID file exists
rm -f "$EXIT_FLAG_FILE" "$PYTHON_PID_FILE" "$BRANCH_REQUEST_FILE"

# load env file, if it exists
file_path=secret.txt
if [ -f "$file_path" ]; then
  source "$file_path" # Or use . "$file_path"
  echo "File '$file_path' sourced successfully."
else
  echo "File '$file_path' does not exist or is not a regular file."
  /bin/bash
fi

# Function to run the Python script
run_python_script() {
    python3 "$PYTHON_SCRIPT" &
    echo $! > "$PYTHON_PID_FILE"
    wait $(cat "$PYTHON_PID_FILE")
    EXIT_CODE=$?
    if [ "$EXIT_CODE" -eq "$BRANCH_SWITCH_EXIT_CODE" ]; then
        echo "Python script requested a branch switch."
        return
    fi
    if [ $EXIT_CODE -ne 143 ]; then
        echo "Python script exited with code $EXIT_CODE. Setting exit flag."
        echo "true" > "$EXIT_FLAG_FILE"
    fi
}

switch_git_branch() {
    REQUESTED_BRANCH="$1"
    git fetch origin > /dev/null 2>&1 || return 1

    if ! git show-ref --verify --quiet "refs/remotes/origin/$REQUESTED_BRANCH"; then
        echo "Requested branch '$REQUESTED_BRANCH' was not found on origin."
        return 1
    fi

    git checkout "$REQUESTED_BRANCH" > /dev/null 2>&1 \
        || git checkout -B "$REQUESTED_BRANCH" "origin/$REQUESTED_BRANCH" > /dev/null 2>&1 \
        || return 1
    git reset --hard "origin/$REQUESTED_BRANCH" > /dev/null 2>&1 || return 1
    git submodule update --init --recursive > /dev/null 2>&1 || return 1
    export GIT_REPO_BRANCH="$REQUESTED_BRANCH"
}

handle_branch_request() {
    if [ ! -f "$BRANCH_REQUEST_FILE" ]; then
        return 1
    fi

    REQUESTED_BRANCH=$(tr -d '\r\n' < "$BRANCH_REQUEST_FILE")
    rm -f "$BRANCH_REQUEST_FILE"

    if [ -z "$REQUESTED_BRANCH" ]; then
        echo "Ignoring empty branch switch request."
        return 1
    fi

    echo "Switching repo to branch '$REQUESTED_BRANCH'..."
    if ! switch_git_branch "$REQUESTED_BRANCH"; then
        echo "Failed to switch to branch '$REQUESTED_BRANCH'. Exiting wrapper."
        echo "true" > "$EXIT_FLAG_FILE"
        return 1
    fi

    echo "Branch switch complete. Relaunching Python script..."
    run_python_script &
    return 0
}

# Trap to clean up background processes and files on exit
trap "kill \$(cat $PYTHON_PID_FILE 2>/dev/null) 2>/dev/null; rm -f \"$EXIT_FLAG_FILE\" \"$PYTHON_PID_FILE\" \"$BRANCH_REQUEST_FILE\"" EXIT

# Start the Python script initially
run_python_script &

# Monitor the GitHub repo for updates
while :; do
    if handle_branch_request; then
        continue
    fi

    if [ -f "$EXIT_FLAG_FILE" ]; then
        echo "Exit flag is set. Exiting bash script."
        exit 1
    fi

    sleep "$CHECK_INTERVAL"

    if handle_branch_request; then
        continue
    fi

    git remote update > /dev/null 2>&1

    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})

    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "Updates detected in the GitHub repository. Pulling changes..."
        git pull > /dev/null 2>&1

        echo "Relaunching the Python script..."
        kill $(cat "$PYTHON_PID_FILE" 2>/dev/null) 2>/dev/null
        run_python_script &
    fi

done
