#!/bin/bash

mkdir -p ${GIT_REPO_PATH}  
cd ${GIT_REPO_PATH}  

( (git init; git remote add origin ${GIT_REPO_URL}; git fetch; git checkout -t origin/${GIT_REPO_BRANCH} -f) || true )  
cd ${GIT_REPO_PATH}  
git config --global --add safe.directory ${GIT_REPO_PATH}  
git fetch origin
git reset --hard origin/${GIT_REPO_BRANCH}

pip install -r requirements.txt  
apt -y install $(cat pkglist)  

${GIT_REPO_PATH}/run.sh 