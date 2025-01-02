import os
import re
import time
import base64
import hashlib
import json
from cryptography.fernet import Fernet


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