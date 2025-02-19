#!/bin/bash

# Define variables
PYTHON_SCRIPT="run.py"   # Replace with the name of your Python script
CHECK_INTERVAL=10                # Time interval to check the repo for updates (in seconds)
EXIT_FLAG_FILE="/tmp/exit_flag"  # File used to indicate when the script should exit
PYTHON_PID_FILE="/tmp/python_pid" # File used to store the Python script's PID
PYTHONPATH=${PYTHONPATH}:$(pwd)/signalbot_local/

echo PYTHONPATH is ${PYTHONPATH}

# Ensure no leftover flag or PID file exists
rm -f "$EXIT_FLAG_FILE" "$PYTHON_PID_FILE"

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
    if [ $EXIT_CODE -ne 143 ]; then
        echo "Python script exited with code $EXIT_CODE. Setting exit flag."
        echo "true" > "$EXIT_FLAG_FILE"
    fi
}

# Trap to clean up background processes and files on exit
trap "kill $(cat $PYTHON_PID_FILE 2>/dev/null) 2>/dev/null; rm -f "$EXIT_FLAG_FILE" "$PYTHON_PID_FILE"" EXIT

# Start the Python script initially
run_python_script &

# Monitor the GitHub repo for updates
while :; do
    if [ -f "$EXIT_FLAG_FILE" ]; then
        echo "Exit flag is set. Exiting bash script."
        exit 1
    fi

    sleep "$CHECK_INTERVAL"
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
