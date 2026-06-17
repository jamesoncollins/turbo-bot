# GPT function tools

The `#gpt` handler can expose local Python functions as model-callable tools. Tool modules live in `tool_functions/` and are loaded dynamically by `handlers/gpt_handler.py`.

## Loader rules

`load_function_tools()` applies these rules:

1. Look in `tool_functions/`.
2. Load files ending in `.py`.
3. Skip files whose names start with `_`.
4. Import each module.
5. Read `TOOL_SPEC` and `TOOL_FN` from the module.
6. Use `TOOL_SPEC["name"]` as the tool name.
7. Store `TOOL_FN` as the function to execute when the model calls that tool.

Modules missing `TOOL_SPEC`, `TOOL_FN`, or a tool name are skipped with a warning.

## Tool function contract

A tool function should:

- Accept keyword arguments described by `TOOL_SPEC["parameters"]`.
- Validate inputs and raise clear exceptions for invalid data.
- Return a dictionary when possible.
- Include text output under a key such as `text`.
- Include base64 attachments under `attachments` when generating files or images.

Existing examples:

- `tool_functions/coin_flip.py`: simple text result.
- `tool_functions/plot_from_data.py`: generates a plot image attachment.

## Minimal example

```python
from typing import Any, Dict


def add_numbers(a: float, b: float) -> Dict[str, Any]:
    return {"text": f"{a} + {b} = {a + b}", "attachments": []}


TOOL_SPEC: Dict[str, Any] = {
    "type": "function",
    "name": "add_numbers",
    "description": "Add two numbers and return the sum.",
    "parameters": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"},
        },
        "required": ["a", "b"],
    },
}

TOOL_FN = add_numbers
```

## Attachment behavior

When a tool returns base64-encoded attachments, `handlers/gpt_handler.py` collects them and includes them in the Signal response. Keep attachments small enough for Signal to send reliably.

## Safety notes

- Do not expose tools that can run arbitrary shell commands from model-provided arguments.
- Validate URLs, filenames, and numeric ranges.
- Avoid writing secrets or sensitive local files into tool responses.
- Prefer deterministic tools with narrow parameter schemas.
