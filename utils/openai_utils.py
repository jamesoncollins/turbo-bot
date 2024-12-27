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
    # Sanitize session_key to ensure it's a valid filename
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
        str: The assistant's response as a string.
    """
    # Initialize conversation history
    if session_key:
        # Load existing conversation history if session_key is provided
        conversation_history = load_conversation_history(session_key)
    else:
        # Start with a fresh conversation
        conversation_history = []

    # Append user's message to the conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Call the OpenAI API with the conversation history
    response = openai.ChatCompletion.create(
        model=model,
        messages=conversation_history
    )

    # Extract the assistant's response
    assistant_message = response['choices'][0]['message']
    conversation_history.append(assistant_message)

    # Save updated conversation history if session_key is provided
    if session_key:
        save_conversation_history(session_key, conversation_history)

    # Return the assistant's reply
    return assistant_message['content']
