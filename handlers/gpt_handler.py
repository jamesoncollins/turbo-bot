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

# Directory to store conversation histories
HISTORY_DIR = "conversation_histories"
os.makedirs(HISTORY_DIR, exist_ok=True)
MAX_HISTORY_LENGTH = 50

image_generation_models = ["dall-e-2", "dall-e-3"]

class GptHandler(HashtagHandler):

    is_intermediate = False
    
    def get_hashtag(self) -> str:
        return r"#gpt"

    def get_substring_mapping(self) -> dict:
        # Provide mapping and default value for 'model'
        return {0: ("model", "gpt-4o-mini")}

    def get_attachments(self) -> list:
        if self.hashtag_data["model"] == "image":
            self.hashtag_data["model"] = "dall-e-2"            
        if self.hashtag_data["model"] in image_generation_models:
            return submit_gpt_image_gen(self.cleaned_input, None, self.hashtag_data["model"])
        return []

    def get_message(self) -> str:
        if self.hashtag_data.get("model") == "help":
            return self.get_help_text()
        
        if self.hashtag_data["model"] == "image":
            self.hashtag_data["model"] = "dall-e-2"            
        if self.hashtag_data["model"] in image_generation_models:
            return f"GPT Image Prompt {self.input_str}"
        
        return submit_gpt(self.cleaned_input, None, self.hashtag_data["model"])
        
    def get_help_text(self) -> str:
        retval = "The first substring specifies the model being used, e.g., #gpt.gpt-4o-mini.\n"
        retval += "Available models are:    \n"
        
        models = client.models.list()
        for model in models:
            retval+=model.id
            retval+="    \n"
            
        retval += "Models that support image generation are:\n"
        retval += '    \n'.join(str(x) for x in image_generation_models)

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

def submit_gpt(user_input, session_key=None, model="gpt-4o-mini"):
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
    # Initialize conversation history
    if session_key:
        conversation_history = load_conversation_history(session_key)
    else:
        conversation_history = []

    # Append user's message to the conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Format the conversation history for the new API
    formatted_messages = [
        {"role": msg["role"], "content": msg["content"]} for msg in conversation_history
    ]

    # Call the OpenAI API with the conversation history
    try:
        response = client.chat.completions.create(model=model, messages=formatted_messages)
    except Exception as e:
        # Code to handle the exception
        print(f"An error occurred: {e}")
        return f"An error occurred: {e}"

    # Extract the assistant's response
    assistant_message = response.choices[0].message
    conversation_history.append(assistant_message)

    # Save updated conversation history if session_key is provided
    if session_key:
        save_conversation_history(session_key, conversation_history)

    # Prepare model details
    model_details = {
        "model": response.model,
        "usage": response.usage.total_tokens,
        "session_key": session_key,
    }

    # Format the details for inclusion in the response string
    details_string = (
        f"\n\nModel: {model_details['model']}\n"
        f"Session Key: {model_details['session_key']}\n"
        f"Token Usage: {model_details['usage']}"
    )

    # Return the assistant's reply with model details
    return assistant_message.content + details_string

def submit_gpt_image_gen(user_input, session_key=None, model="dall-e-2"):

    if session_key:
        return []
    
    response = client.images.generate(
        model=model,
        prompt=user_input,
        n=1,
        #size="256x256",
        response_format="b64_json",
    )
    print(response.data[0].revised_prompt)
    #print(response.data[0].url)
    return [response.data[0].b64_json]




def string_to_base64_text_file(input_string):
    """
    Creates a Base64-encoded text file from a string without saving it to disk.
    
    :param input_string: The string to encode.
    :return: A bytes object representing the Base64-encoded text file.
    """
    # Encode the string to Base64
    b64_encoded = base64.b64encode(input_string.encode('utf-8'))

    # Create a virtual file
    virtual_file = io.BytesIO()
    virtual_file.write(b64_encoded)
    virtual_file.seek(0)  # Rewind the file to the beginning
    
    # Get the contents of the virtual file as bytes
    return virtual_file.read()

# Example usage
encoded_file_content = string_to_base64_text_file("Hello, World!")
print(encoded_file_content)  # This is the Base64-encoded representation of the text file
    