# handlers/gpt_handler.py
from handlers.hashtag_handler import HashtagHandler
import os
import json
import re
from openai import OpenAI
import importlib.util
import warnings
import base64

key = os.environ.get("OPENAI_API_KEY", "")
if key == "":
    warnings.warn("Warning...........No OPENAI_API_KEY provided")
client = OpenAI(api_key=key)

DEFAULT_MODEL = "gpt-4.1"
DEFAULT_IMAGE_MODEL = "dall-e-3"
IMAGE_MODEL_PREFIXES = ("chatgpt-image-", "gpt-image-", "dall-e-")
TOOL_DIR = os.path.join(os.path.dirname(__file__), "..", "tool_functions")

HISTORY_DIR = "conversation_histories"
os.makedirs(HISTORY_DIR, exist_ok=True)
MAX_HISTORY_LENGTH = 50

WEB_SEARCH_TOOL = {"type": "web_search", "search_context_size": "high"}
WEB_SEARCH_TOOL_CHOICE = {
    "type": "allowed_tools",
    "mode": "required",
    "tools": [{"type": "web_search"}],
}
WEB_SEARCH_GUIDANCE = (
    "You are a helpful chatbot for signal groups. Single-shot only: answer in one reply "
    "and do not ask follow-up questions. If details are missing, make reasonable "
    "assumptions and state them briefly. Be concise and direct; use bullet points only "
    "when they improve clarity. Never invent numbers, dates, or factual data. If tool "
    "inputs are missing, do NOT call function tools; respond with plain text instead. "
    "When calling function tools, always include all required arguments per the tool "
    "schema; never call a function tool with empty arguments. Web-search bias: for any "
    "request about specific facts, named entities, events, products, prices, schedules, "
    "laws, recommendations, health, finance, technical documentation, or anything that "
    "might have changed recently, prefer web_search before answering even if you think "
    "you already know the answer. You MUST use web_search first for time-sensitive or "
    "current information (e.g., today, latest, news, weather, prices, schedules, scores, "
    "versions, availability), and base the answer only on returned sources. If "
    "web_search does not return relevant results, say you could not find the data instead "
    "of guessing. Use internal knowledge without web_search only for clearly timeless, "
    "creative, personal, or purely conversational requests. If sources are provided, "
    "incorporate them in the answer when relevant."
)
WEB_SEARCH_FORCE_TERMS = (
    "latest",
    "current",
    "currently",
    "today",
    "tonight",
    "tomorrow",
    "yesterday",
    "this week",
    "this month",
    "this year",
    "recent",
    "recently",
    "news",
    "headline",
    "update",
    "weather",
    "forecast",
    "price",
    "prices",
    "cost",
    "stock",
    "ticker",
    "market",
    "exchange rate",
    "schedule",
    "score",
    "standings",
    "available",
    "availability",
    "version",
    "release",
    "changelog",
    "law",
    "legal",
    "regulation",
    "policy",
    "recommend",
    "best",
    "review",
    "compare",
    "restaurant",
    "travel",
    "flight",
    "hotel",
    "election",
    "president",
    "ceo",
    "who won",
    "when is",
    "where is",
    "how much",
)
WEB_SEARCH_FORCE_PREFIXES = (
    "who is ",
    "who are ",
    "what is the latest",
    "what are the latest",
    "what happened",
    "where can i",
    "where should i",
    "should i buy",
)


class GptHandler(HashtagHandler):

    is_intermediate = False

    def get_hashtag(self) -> str:
        return r"#gpt"

    def get_substring_mapping(self) -> dict:
        return {0: ("model", DEFAULT_MODEL)}

    def process_message(self, msg, attachments):

        if self.hashtag_data.get("model") == "help":
            return {"message": self.get_help_text(), "attachments": []}

        if self.hashtag_data["model"] == "image":
            self.hashtag_data["model"] = DEFAULT_IMAGE_MODEL

        if is_image_model(self.hashtag_data["model"]):
            return submit_gpt_image_gen(self.cleaned_input, None, self.hashtag_data["model"])

        if self.hashtag_data["model"] == "read":
            url = self.extract_url(msg)
            url_text = extract_text_from_url(url)
            msg = "Please summarize this text:\n" + url_text
            return submit_gpt(msg, None, DEFAULT_MODEL)

        return submit_gpt(self.cleaned_input, None, self.hashtag_data["model"])

    @staticmethod
    def get_help_text() -> str:
        retval = "The first substring specifies the model being used, e.g., #gpt.gpt-4o-mini.\n"
        retval += "Use #gpt.image to generate an image with the default image model.\n"
        retval += "Image model prefixes: chatgpt-image-*, gpt-image-*, dall-e-*.\n"
        retval += "Available models are:    \n"

        models = client.models.list()
        for model in models:
            retval += model.id
            retval += "    \n"

        function_tools, _ = load_function_tools()
        tool_lines = []
        for tool in function_tools:
            name = tool.get("name")
            desc = tool.get("description")
            if name:
                tool_lines.append(f"{name} - {desc}" if desc else name)
        tool_lines.sort()

        retval += "Available function tools are:    \n"
        retval += "\n".join(tool_lines) + "    \n" if tool_lines else "none    \n"
        return retval

    @staticmethod
    def get_name() -> str:
        return "GptHandler"


def load_function_tools():
    tool_specs = []
    tool_fns = {}
    if not os.path.isdir(TOOL_DIR):
        return tool_specs, tool_fns

    for filename in os.listdir(TOOL_DIR):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue
        module_path = os.path.join(TOOL_DIR, filename)
        module_name = f"tool_functions.{os.path.splitext(filename)[0]}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            warnings.warn(f"Skipping tool module without spec: {module_path}")
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            warnings.warn(f"Failed to load tool module {module_path}: {e}")
            continue

        tool_spec = getattr(module, "TOOL_SPEC", None)
        tool_fn = getattr(module, "TOOL_FN", None)
        if not tool_spec or not tool_fn:
            warnings.warn(f"Missing TOOL_SPEC or TOOL_FN in {module_path}")
            continue

        tool_name = tool_spec.get("name")
        if not tool_name:
            warnings.warn(f"Missing tool name in {module_path}")
            continue

        tool_specs.append(tool_spec)
        tool_fns[tool_name] = tool_fn

    return tool_specs, tool_fns


def build_function_tool_outputs(response, tool_fns):
    tool_outputs = []
    tool_attachments = []
    tool_errors = []
    tool_calls_debug = []

    output = getattr(response, "output", None) or []
    for item in output:
        item_type = getattr(item, "type", None)
        if item_type is None and isinstance(item, dict):
            item_type = item.get("type")
        if item_type != "function_call":
            continue

        tool_name = getattr(item, "name", None)
        if tool_name is None and isinstance(item, dict):
            tool_name = item.get("name")

        call_id = getattr(item, "call_id", None)
        if call_id is None and isinstance(item, dict):
            call_id = item.get("call_id")

        args_raw = getattr(item, "arguments", None)
        if args_raw is None and isinstance(item, dict):
            args_raw = item.get("arguments")

        tool_calls_debug.append({"tool": tool_name, "arguments": args_raw})

        try:
            args = json.loads(args_raw or "{}")
        except Exception as e:
            result = f"ERROR: Invalid JSON arguments for {tool_name}: {e}"
            tool_errors.append(result)
            tool_outputs.append({"type": "function_call_output", "call_id": call_id, "output": result})
            continue

        if not isinstance(args, dict) or len(args) == 0:
            result = (
                f"ERROR: Empty arguments for tool {tool_name}. "
                f"Do not call this tool unless you can provide all required fields."
            )
            tool_errors.append(result)
            tool_outputs.append({"type": "function_call_output", "call_id": call_id, "output": result})
            continue

        tool_fn = tool_fns.get(tool_name)
        if tool_fn is None:
            result = f"ERROR: Unknown tool {tool_name}"
            tool_errors.append(result)
            tool_outputs.append({"type": "function_call_output", "call_id": call_id, "output": result})
            continue

        try:
            result = tool_fn(**args)
        except Exception as e:
            result = f"ERROR: {type(e).__name__}: {e}"
            tool_errors.append(result)

        output_text = result
        if isinstance(result, dict):
            attachments = result.get("attachments")
            if isinstance(attachments, list):
                tool_attachments.extend(attachments)
            output_text = result.get("text", "OK")
        elif not isinstance(result, str):
            output_text = json.dumps(result, default=str)

        tool_outputs.append({"type": "function_call_output", "call_id": call_id, "output": output_text})

    return tool_outputs, tool_attachments, tool_errors, tool_calls_debug


def get_used_tools(response):
    tools = []
    output = getattr(response, "output", None) or []
    for item in output:
        item_type = getattr(item, "type", None)
        if item_type is None and isinstance(item, dict):
            item_type = item.get("type")

        tool_name = None
        if item_type == "function_call":
            tool_name = getattr(item, "name", None)
            if tool_name is None and isinstance(item, dict):
                tool_name = item.get("name")
        elif item_type and item_type.endswith("_call"):
            tool_name = item_type[:-5]

        if tool_name:
            tools.append(tool_name)

    seen = set()
    unique_tools = []
    for t in tools:
        if t not in seen:
            unique_tools.append(t)
            seen.add(t)
    return unique_tools


def should_force_web_search(user_input: str) -> bool:
    """Return True when the first model turn should be required to search the web."""
    if not user_input:
        return False

    normalized = " ".join(user_input.lower().split())
    if "http://" in normalized or "https://" in normalized:
        return True

    if any(normalized.startswith(prefix) for prefix in WEB_SEARCH_FORCE_PREFIXES):
        return True

    if any(re.search(rf"\b{re.escape(term)}\b", normalized) for term in WEB_SEARCH_FORCE_TERMS):
        return True

    # Years and date-like prompts are often asking for facts that may be stale in model memory.
    if any(str(year) in normalized for year in range(2024, 2031)):
        return True

    return False


def build_response_create_kwargs(model, tools, input_data, force_web_search=False, previous_response_id=None):
    kwargs = {
        "model": model,
        "tools": tools,
        "input": input_data,
        "include": ["web_search_call.action.sources"],
    }
    if previous_response_id is not None:
        kwargs["previous_response_id"] = previous_response_id
    if force_web_search:
        kwargs["tool_choice"] = WEB_SEARCH_TOOL_CHOICE
    return kwargs


def submit_gpt(user_input, session_key=None, model=DEFAULT_MODEL):
    json_session = []

    if len(json_session) == 0:
        json_session.append(
            {
                "role": "system",
                "content": WEB_SEARCH_GUIDANCE,
            }
        )

    json_session.append({"role": "user", "content": user_input})
    formatted_messages = [{"role": msg["role"], "content": msg["content"]} for msg in json_session]

    function_tools, function_tool_fns = load_function_tools()
    tools = [WEB_SEARCH_TOOL] + function_tools
    force_web_search = should_force_web_search(user_input)

    try:
        response = client.responses.create(
            **build_response_create_kwargs(
                model=model,
                tools=tools,
                input_data=formatted_messages,
                force_web_search=force_web_search,
            )
        )
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"message": f"An error occurred: {e}", "attachments": []}

    response_steps = 0
    function_tool_calls = 0
    tool_loop_truncated = False
    tools_used_all = []
    tool_attachments = []
    tool_errors = []
    tool_calls_debug = []

    max_tool_steps = 100
    while True:
        response_steps += 1
        tools_used_all += get_used_tools(response)

        tool_outputs, step_attachments, step_errors, step_calls_debug = build_function_tool_outputs(response, function_tool_fns)
        function_tool_calls += len(tool_outputs)
        tool_attachments += step_attachments
        tool_errors += step_errors
        tool_calls_debug += step_calls_debug

        if not tool_outputs:
            break

        if response_steps >= max_tool_steps:
            tool_loop_truncated = True
            break

        response = client.responses.create(
            **build_response_create_kwargs(
                model=model,
                tools=tools,
                previous_response_id=response.id,
                input_data=tool_outputs,
            )
        )

    assistant_text = response.output_text
    json_session.append({"role": "assistant", "content": assistant_text})

    seen = set()
    tools_used_unique = []
    for t in tools_used_all:
        if t not in seen:
            tools_used_unique.append(t)
            seen.add(t)

    model_details = {
        "model": response.model,
        "usage": response.usage.total_tokens,
        "session_key": session_key,
    }

    details_string = (
        f"\n\nModel: {model_details['model']}\n"
        f"Session Key: {model_details['session_key']}\n"
        f"Token Usage: {model_details['usage']}\n"
        f"Tools Used: {tools_used_unique}\n"
        f"Web Search Forced: {force_web_search}\n"
        f"Function Calls Executed: {function_tool_calls}\n"
        f"Response Steps: {response_steps}\n"
        f"Tool Loop Truncated: {tool_loop_truncated}\n"
        f"Tool Attachments: {len(tool_attachments)}\n"
        f"Tool Errors: {tool_errors if tool_errors else 'none'}\n"
        f"Tool Calls: {tool_calls_debug if tool_calls_debug else 'none'}"
    )

    return {"message": assistant_text + details_string, "attachments": tool_attachments}


def is_image_model(model_name: str) -> bool:
    return any(model_name.startswith(prefix) for prefix in IMAGE_MODEL_PREFIXES)


def submit_gpt_image_gen(user_input, session_key=None, model=DEFAULT_IMAGE_MODEL):
    if session_key:
        return []

    try:
        response = client.images.generate(
            model=model,
            prompt=user_input,
            n=1,
            response_format="b64_json",
        )
    except Exception as e:
        if "Unknown parameter: 'response_format'" in str(e):
            response = client.images.generate(model=model, prompt=user_input, n=1)
        else:
            raise

    image_data = response.data[0]
    image_b64 = getattr(image_data, "b64_json", None)
    if image_b64 is None and isinstance(image_data, dict):
        image_b64 = image_data.get("b64_json")

    if not image_b64:
        image_url = getattr(image_data, "url", None)
        if image_url is None and isinstance(image_data, dict):
            image_url = image_data.get("url")
        if image_url:
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            image_b64 = base64.b64encode(image_response.content).decode("utf-8")

    revised_prompt = getattr(image_data, "revised_prompt", None)
    if revised_prompt is None and isinstance(image_data, dict):
        revised_prompt = image_data.get("revised_prompt")

    return {"message": revised_prompt, "attachments": [image_b64] if image_b64 else []}


import requests
from bs4 import BeautifulSoup


def extract_text_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return ""
