import os
import re
import time
import base64

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
