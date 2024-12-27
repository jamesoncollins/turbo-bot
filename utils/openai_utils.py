import openai
import os
import json

# Directory to store conversation histories
HISTORY_DIR = "conversation_histories"
os.makedirs(HISTORY_DIR, exist_ok=True)

# Use environment variable for OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

def get_history_file_path(session_key):
    """Returns the file path for a given session key."""
    safe_key = "".join(c for c in session_key if c.isalnum() or c in (' ', '.', '_')).rstrip()
    return os.path.join(HISTORY_DIR, f"{safe_key}.json")

def load_conversation_history(session_key):
    """Loads conversation history from a file."""
    history_file = get_history_file_path(session_key)
    if os.path.exists(history_file):
        with open(history_file, "r") as file:
            return json.load(file)
    return []

def save_conversation_history(session_key, history):
    """Saves conversation history to a file."""
    history_file = get_history_file_path(session_key)
    with open(history_file, "w") as file:
        json.dump(history, file, indent=4)

def submit_gpt(user_input, session_key=None, model="gpt-4"):
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
    response = openai.ChatCompletion.create(
        model=model,
        messages=formatted_messages
    )

    # Extract the assistant's response
    assistant_message = response["choices"][0]["message"]
    conversation_history.append(assistant_message)

    # Save updated conversation history if session_key is provided
    if session_key:
        save_conversation_history(session_key, conversation_history)

    # Prepare model details
    model_details = {
        "model": response.get("model", model),
        "usage": response.get("usage", {}),
        "session_key": session_key,
    }

    # Format the details for inclusion in the response string
    details_string = (
        f"\n\nModel: {model_details['model']}\n"
        f"Session Key: {model_details['session_key']}\n"
        f"Token Usage: {model_details['usage']}"
    )

    # Return the assistant's reply with model details
    return assistant_message["content"] + details_string
