#!/bin/bash

# Ensure the GIT_REPO_PATH directory exists
mkdir -p ${GIT_REPO_PATH}  
cd ${GIT_REPO_PATH}  

# Initialize the repository and configure the remote and branch
( (git init; 
    git remote add origin ${GIT_REPO_URL}; 
    git fetch; 
    git checkout -t origin/${GIT_REPO_BRANCH} -f) || true )

# Configure the repository as a safe directory for Git
cd ${GIT_REPO_PATH}  
git config --global --add safe.directory ${GIT_REPO_PATH}  

# Fetch the latest changes and reset to match the remote branch
git fetch origin
git reset --hard origin/${GIT_REPO_BRANCH}

# Initialize and update Git submodules
git submodule update --init --recursive

# Install Python dependencies
pip install -r requirements.txt  

# Install system packages from pkglist
apt -y install $(cat pkglist)  

# Run the main script
${GIT_REPO_PATH}/run.sh
