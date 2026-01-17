# handlers/gpt_handler.py
from handlers.hashtag_handler import HashtagHandler
import os
import json
from openai import OpenAI
import warnings
import base64
import io


key = os.environ.get("OPENAI_API_KEY", "")
if key=="":
    warnings.warn("Warning...........No OPENAI_API_KEY provided")
client = OpenAI(api_key=key)

DEFAULT_MODEL = "gpt-4.1"
DEFAULT_IMAGE_MODEL = "chatgpt-image-latest"
IMAGE_MODEL_PREFIXES = ("chatgpt-image-", "gpt-image-", "dall-e-")

# Directory to store conversation histories
HISTORY_DIR = "conversation_histories"
os.makedirs(HISTORY_DIR, exist_ok=True)
MAX_HISTORY_LENGTH = 50


class GptHandler(HashtagHandler):

    is_intermediate = False
    
    def get_hashtag(self) -> str:
        return r"#gpt"

    def get_substring_mapping(self) -> dict:
        # Provide mapping and default value for 'model'
        return {0: ("model", DEFAULT_MODEL)}

    def process_message(self, msg, attachments):
        
        if self.hashtag_data.get("model") == "help":
            return {"message": self.get_help_text(), "attachments": []}

        if self.hashtag_data["model"] == "image":
            self.hashtag_data["model"] = DEFAULT_IMAGE_MODEL

        if is_image_model(self.hashtag_data["model"]):
            return submit_gpt_image_gen(self.cleaned_input, None, self.hashtag_data["model"])
        
        # try to get quote info.  currently this is a try becuase i dont know
        # how it looks for a data message
        json_quoted_convo = None
        try:
            quote_msg = self.context.message.raw_message["envelope"]["syncMessage"]["sentMessage"]["quote"]
            quote_author = quote_msg["author"]
            quote_text = quote_msg["text"]
            quote_attachments = quote_msg["attachments"]
            convo_b64 = find_first_text_file_base64(quote_attachments)
            json_quoted_convo = base64_text_file_to_json(convo_b64)
        except:
            pass
        
        if self.hashtag_data["model"] == "read":
            url = self.extract_url(msg)
            url_text = extract_text_from_url(url)
            msg = "Please summarize this text:\n" + url_text;
            return submit_gpt(msg, json_quoted_convo, None, DEFAULT_MODEL)
       
        return submit_gpt(self.cleaned_input, json_quoted_convo, None, self.hashtag_data["model"])

    @staticmethod    
    def get_help_text() -> str:
        retval = "The first substring specifies the model being used, e.g., #gpt.gpt-4o-mini.\n"
        retval += "Use #gpt.image to generate an image with the default image model.\n"
        retval += "Image model prefixes: chatgpt-image-*, gpt-image-*, dall-e-*.\n"
        retval += "Available models are:    \n"
        
        models = client.models.list()
        for model in models:
            retval+=model.id
            retval+="    \n"

        return retval

    @staticmethod
    def get_name() -> str:
        return "GptHandler"
    
def get_history_file_path(session_key):
    """Returns the file path for a given session key."""
    safe_key = "".join(c for c in session_key if c.isalnum() or c in (' ', '.', '_')).rstrip()
    return os.path.join(HISTORY_DIR, f"{safe_key}.json")

def load_conversation_history(session_key):
    """Loads conversation history from a file."""
    history_file = get_history_file_path(session_key)
    if os.path.exists(history_file):
        with open(history_file, "r") as file:
            history = json.load(file)
        # Ensure the history format is valid
        return history
    return []

def save_conversation_history(session_key, history):
    """Saves conversation history to a file with a limit on history length."""
    history_file = get_history_file_path(session_key)
    # Keep only the most recent messages within the limit
    trimmed_history = history[-MAX_HISTORY_LENGTH:]
    with open(history_file, "w") as file:
        json.dump(trimmed_history, file, indent=4)

def get_used_tools(response):
    tools = []
    output = getattr(response, "output", None) or []
    for item in output:
        item_type = getattr(item, "type", None)
        if item_type is None and isinstance(item, dict):
            item_type = item.get("type")
        tool_name = None
        if item_type == "tool_call":
            tool_name = getattr(item, "name", None)
            if tool_name is None and isinstance(item, dict):
                tool_name = item.get("name")
        elif item_type == "function_call":
            tool_name = getattr(item, "name", None)
            if tool_name is None and isinstance(item, dict):
                tool_name = item.get("name")
            if tool_name is None:
                tool_name = "function"
        elif item_type and item_type.endswith("_call"):
            tool_name = item_type[:-5]
        if tool_name:
            tools.append(tool_name)
    seen = set()
    unique_tools = []
    for tool in tools:
        if tool not in seen:
            unique_tools.append(tool)
            seen.add(tool)
    return unique_tools

def submit_gpt(user_input, json_session = None, session_key=None, model=DEFAULT_MODEL):
    """
    Submits user input to the GPT model, maintaining conversation history.
    
    Parameters:
        user_input (str): The input message from the user.
        session_key (str): The unique session key to identify the conversation. 
                           If None or empty, no history is loaded or saved.
        model (str): The model to use (default: "gpt-4").
        
    Returns:
        str: The assistant's response along with model details.
    """
    if not json_session:
        json_session = []
    
    
    # control the gpt system prompts.
    # this is the spot you might use for having different personailities    
    if len(json_session) == 0:
        json_session.append({"role": "system", "content": 
             "You are a helpful chatbot for signal groups."
                             }
        )
        
    # Append user's message to the conversation history
    json_session.append({"role": "user", "content": user_input})

    # Format the conversation history for the new API
    formatted_messages = [
        {"role": msg["role"], "content": msg["content"]} for msg in json_session
    ]

    # Call the OpenAI API with the conversation history
    try:
        response = client.responses.create(
            model=model,
            tools=[
                {"type": "web_search"}
                ],
            input=formatted_messages,
            include=["web_search_call.action.sources"],
        )
    except Exception as e:
        # Code to handle the exception
        print(f"An error occurred: {e}")
        return {"message": f"An error occurred: {e}", "attachments": []}
    
    # Extract the assistant's response
    assistant_text = response.output_text
    json_session.append({"role": "assistant", "content": assistant_text})

    print(json_session)

    # Prepare model details
    tools_used = get_used_tools(response)
    tools_text = ", ".join(tools_used) if tools_used else "none"
    model_details = {
        "model": response.model,
        "usage": response.usage.total_tokens,
        "session_key": session_key,
    }

    # Format the details for inclusion in the response string
    details_string = (
        f"\n\nModel: {model_details['model']}\n"
        f"Session Key: {model_details['session_key']}\n"
        f"Token Usage: {model_details['usage']}\n"
        f"Tools Used: {tools_text}"
    )
        

    # Return the assistant's reply with model details
    return {"message": assistant_text + details_string, "attachments": [json_to_base64_text_file(json_session)]}

def is_image_model(model_name: str) -> bool:
    return any(model_name.startswith(prefix) for prefix in IMAGE_MODEL_PREFIXES)

def submit_gpt_image_gen(user_input, session_key=None, model=DEFAULT_IMAGE_MODEL):

    if session_key:
        return []

    response = client.images.generate(
        model=model,
        prompt=user_input,
        n=1,
        #size="256x256",
        response_format="b64_json",
    )

    return { "message": response.data[0].revised_prompt, "attachments": [response.data[0].b64_json] }



def json_to_base64_text_file(json_data):

    try:
        input_data = json.dumps(json_data)
        
        # Convert the input string to bytes
        input_bytes = input_data.encode('utf-8')

        # Encode the bytes to Base64
        base64_encoded = base64.b64encode(input_bytes).decode('utf-8')
        return base64_encoded
        
        # Construct the MIME data
        mime_type = "text/plain"        
        mime_data = f"data:{mime_type};name=log.txt;base64,{base64_encoded}"
        
        # Return MIME data as bytes
        return mime_data.encode('utf-8')
    except Exception as e:
        raise ValueError(f"An error occurred: {e}")

def base64_text_file_to_json(b64_file_content):
    """
    Decodes a Base64-encoded text file and converts it back to JSON data.
    
    :param b64_file_content: The Base64-encoded content of the text file (bytes object).
    :return: The decoded JSON data as a Python dictionary or list.
    """
    # Decode the Base64 content to get the original JSON string
    decoded_bytes = base64.b64decode(b64_file_content)
    json_string = decoded_bytes.decode('utf-8')
    
    # Parse the JSON string back into a Python object
    json_data = json.loads(json_string)
    
    print(f"loaded json data {json_data}")
    
    return json_data

def find_first_text_file_base64(base64_files):
    """
    Identifies the first Base64-encoded file in the list that is a text file and returns it.
    
    :param base64_files: A list of Base64-encoded file contents (as bytes or strings).
    :return: The Base64 string representing the first text file found, or None if no text file is found.
    """
    for b64_file in base64_files:
        try:
            # Decode the Base64 content
            decoded_bytes = base64.b64decode(b64_file)

            # Attempt to decode the bytes as UTF-8 (text)
            decoded_text = decoded_bytes.decode('utf-8')
            
            #if contentType == "application/json":
            #    return decoded_bytes.decode('utf-8')

            # If successful, return the original Base64 string
            return b64_file
        except (base64.binascii.Error, UnicodeDecodeError):
            # If decoding fails, it's not a valid Base64 or not a text file
            continue

    # Return None if no text file is found
    return None
    
import requests
from bs4 import BeautifulSoup

def extract_text_from_url(url):
    try:
        # Send HTTP request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract and return all text
        return soup.get_text(separator='\n', strip=True)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return ""


