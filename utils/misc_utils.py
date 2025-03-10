import os
import re
import time
import base64
import hashlib
import json
from cryptography.fernet import Fernet
import git
from datetime import datetime
import ffmpeg

# Append a dictionary to the JSON file
def append_to_json_file(file_path, new_data, encryption_key=None):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        # Read the existing data from the file
        with open(file_path, "rb" if encryption_key else "r") as file:
            if encryption_key:
                fernet = Fernet(encryption_key)
                encrypted_data = file.read()
                data = json.loads(fernet.decrypt(encrypted_data).decode())
            else:
                data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # Initialize an empty list if the file doesn't exist or is invalid
        data = []

    # Append the new data to the existing list
    data.append(new_data)

    # Write the updated list back to the file
    with open(file_path, "wb" if encryption_key else "w") as file:
        if encryption_key:
            fernet = Fernet(encryption_key)
            encrypted_data = fernet.encrypt(json.dumps(data).encode())
            file.write(encrypted_data)
        else:
            json.dump(data, file, indent=4)

# Retrieve and return the contents of the JSON file as a string
def get_json_file_contents(file_path, encryption_key=None):
    try:
        # Read the JSON file
        with open(file_path, "rb" if encryption_key else "r") as file:
            if encryption_key:
                fernet = Fernet(encryption_key)
                encrypted_data = file.read()
                data = json.loads(fernet.decrypt(encrypted_data).decode())
            else:
                data = json.load(file)
        
        # Prepare the data as a string
        contents = "Contents:\n"
        contents += "\n".join([str(item) for item in data])
        return contents
    except (FileNotFoundError, json.JSONDecodeError):
        return "The file does not exist or is invalid."
def hash_string(group_id):
    return hashlib.sha256(group_id.encode()).hexdigest()

def file_to_base64(file_path):
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)
            base64_string = encoded_content.decode('utf-8')
            return base64_string
    except FileNotFoundError:
        return f"Error: File not found at path: {file_path}"



def extract_url(text, domain):
    pattern = r"https?://(?:www\.)?" + re.escape(domain) + r"(/[^\s]*)?"
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return None

  

def print_file(file_path):
    try:
        with open(file_path, 'r') as file:
            # Read the content of the file
            file_content = file.read()
            
            # Print the content
            #print(&quot;File Content:\n&quot;, file_content)
            
            return file_content

    except FileNotFoundError:
        pass #print(f&quot;File '{file_path}' not found.&quot;)
    except Exception as e:
        pass #print(f&quot;An error occurred: {e}&quot;)
        
    return None


def parse_env_var(env_var, delimiter=";"):
    """
    Parses an environment variable and returns a list, a boolean, or None.
    
    Args:
        env_var (str): The name of the environment variable.
        delimiter (str): The delimiter used for splitting lists.
        
    Returns:
        list, bool, or None: Parsed value from the environment variable.
    """
    value = os.environ.get(env_var, None)
    if value is None or value.strip() == "":
        return None  # Treat as "not supplied"
    
    #value = value.strip().lower()
    
    if value in {"true", "false"}:
        return value == "true"  # Return as a Python boolean
    elif delimiter in value:
        return value.split(delimiter)  # Return as a list
    else:
        return [value]  # Single value as a list
    
def get_git_info():
    """
    Retrieves the current branch name, commit ID, timestamp, and committer name
    of the latest commit from the Git repository.

    Returns:
        str: A formatted string with the branch name, commit ID, timestamp, and committer name
             on separate lines. Returns "Not a Git repository" if not in a Git repository.
    """
    try:
        repo = git.Repo(os.path.dirname(os.path.abspath(__file__)), search_parent_directories=True)
        branch_name = repo.active_branch.name
        commit_id = repo.head.commit.hexsha
        commit_time = datetime.fromtimestamp(repo.head.commit.committed_date).strftime('%Y-%m-%d %H:%M:%S')
        committer_name = repo.head.commit.committer.name

        return (f"Branch: {branch_name}\n"
                f"Commit ID: {commit_id}\n"
                f"Timestamp: {commit_time}\n"
                f"Committer: {committer_name}")
    except git.InvalidGitRepositoryError:
        return "Not a Git repository"


def convert_to_mp4(input_file: str, output_file: str, max_size_mb: int, max_resolution: tuple = (1280, 720)):
    """
    Convert a video file to MP4 format while ensuring it does not exceed a specified file size
    and optionally limiting the maximum resolution. If the input file is already MP4 and within
    the size limit, no conversion is performed.

    Parameters:
    - input_file (str): Path to the input video file.
    - output_file (str): Path to save the converted MP4 file.
    - max_size_mb (int): Maximum size of the output file in megabytes.
    - max_resolution (tuple): Maximum resolution (width, height) for the output video.

    Returns:
    - str: Path to the converted file (or the original file if no conversion was needed).
    """
    # Get input file metadata
    probe = ffmpeg.probe(input_file)
    file_format = probe['format']['format_name']
    duration = float(probe['format']['duration'])  # Video duration in seconds
    file_size_mb = int(probe['format']['size']) / (1024 * 1024)  # Convert size to MB

    # If the file is already MP4 and within the size limit, return the original file
    if file_format == "mov,mp4,m4a,3gp,3g2,mj2" and file_size_mb <= max_size_mb:
        print(f"Skipping conversion: {input_file} is already an MP4 and under {max_size_mb} MB.")
        return input_file

    # Get original video dimensions
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    if not video_stream:
        raise ValueError("No video stream found in the input file.")

    original_width = int(video_stream['width'])
    original_height = int(video_stream['height'])

    # Calculate target bitrate (bits per second) to fit within max size
    max_size_bytes = max_size_mb * 1024 * 1024
    bitrate = (max_size_bytes * 8) / duration  # bits per second

    # Ensure a minimum bitrate threshold
    min_bitrate = 150000  # 150 kbps
    bitrate = max(bitrate, min_bitrate)

    # Adjust resolution if it exceeds max_resolution
    target_width, target_height = original_width, original_height
    if original_width > max_resolution[0] or original_height > max_resolution[1]:
        scale_factor = min(max_resolution[0] / original_width, max_resolution[1] / original_height)
        target_width = int(original_width * scale_factor)
        target_height = int(original_height * scale_factor)

        # Ensure width and height are even numbers (required by some codecs)
        target_width = target_width if target_width % 2 == 0 else target_width - 1
        target_height = target_height if target_height % 2 == 0 else target_height - 1

    # Convert video using calculated bitrate and resolution
    ffmpeg.input(input_file).output(
        output_file,
        vcodec="libx264",
        acodec="aac",
        video_bitrate=int(bitrate),
        audio_bitrate="128k",
        vf=f"scale={target_width}:{target_height}",
        format="mp4"
    ).run(overwrite_output=True)

    return output_file

# Example usage:
# convert_to_mp4("input.avi", "output.mp4", max_size_mb=50, max_resolution=(1280, 720))
