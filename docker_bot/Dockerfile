FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip git ffmpeg 

# Download the requirements.txt from GitHub
RUN apt-get update && apt-get install -y curl && \
    curl -o requirements.txt https://raw.githubusercontent.com/jamesoncollins/turbo-bot/refs/heads/main/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt