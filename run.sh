#!/bin/bash

echo "Run script started with PID $$"

# Define variables
PYTHON_SCRIPT="run.py"   # Replace with the name of your Python script
CHECK_INTERVAL=15                # Time interval to check the repo for updates (in seconds)
EXIT_FLAG=false                  # Global flag to indicate when the script should exit

# Function to run the Python script
run_python_script() {
    EXIT_FLAG=false 
    python3 "$PYTHON_SCRIPT" &
    PYTHON_PID=$!
	echo "script launched with pid ${PYTHON_PID}"
    wait "$PYTHON_PID"
    EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        echo "Python script exited with code $EXIT_CODE. Setting exit flag."
        EXIT_FLAG=true
		exit 1
    fi
}

# Trap to clean up background processes on exit
trap "kill 0" EXIT

# Start the Python script initially
run_python_script &

# Monitor the GitHub repo for updates
while :; do

    sleep "$CHECK_INTERVAL"
	
	if [ "$EXIT_FLAG" = true ]; then
        echo "Exit flag is set. Exiting bash script."
        exit 1
    fi
	
    echo "exit flag not set"
	
    #git remote update > /dev/null 2>&1

    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})

    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "Updates detected in the GitHub repository. Pulling changes..."
        git pull > /dev/null 2>&1

        echo "Killing PID ${PYTHON_PID} and Relaunching the Python script..."
        kill "$PYTHON_PID" 2>/dev/null
        run_python_script &
    fi

done
