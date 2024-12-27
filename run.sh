#!/bin/bash

# Define variables
PYTHON_SCRIPT="run.py"   # Replace with the name of your Python script
CHECK_INTERVAL=60                # Time interval to check the repo for updates (in seconds)

# Function to run the Python script
run_python_script() {
    python3 "$PYTHON_SCRIPT" &
    PYTHON_PID=$!
    wait $PYTHON_PID
    exit 1  # Exit the script if the Python script terminates
}

# Trap to clean up background processes on exit
trap "kill 0" EXIT

# Start the Python script
run_python_script &

# Monitor the GitHub repo for updates
while :; do
    sleep "$CHECK_INTERVAL"
    git remote update > /dev/null 2>&1

    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})

    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "Updates detected in the GitHub repository. Pulling changes..."
        git pull > /dev/null 2>&1

        echo "Relaunching the Python script..."
        kill "$PYTHON_PID"
        run_python_script &
    fi

done
