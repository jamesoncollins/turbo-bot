# Writing handlers

Handlers are the main extension point for TurboBot. A handler decides whether it can process an incoming Signal message and, if so, returns text and optional base64 attachments for the bot to send.

## Choosing a base class

Use `BaseHandler` directly when matching arbitrary message text, URLs, or attachments.

Use `HashtagHandler` when implementing command-style features such as:

- `#gpt`
- `#mmw`
- `#golf`
- `#asteroid`
- `#numberwang`

`HashtagHandler` handles command detection, dot-separated substring parsing, and cleaned input extraction.

## BaseHandler contract

A direct `BaseHandler` subclass should usually implement:

```python
from handlers.base_handler import BaseHandler


class MyHandler(BaseHandler):
    def can_handle(self) -> bool:
        return "hello bot" in self.input_str.lower()

    def process_message(self, msg, attachments):
        return {
            "message": "Hello from TurboBot!",
            "attachments": [],
        }

    @staticmethod
    def get_name() -> str:
        return "My Handler"

    @staticmethod
    def get_help_text() -> str:
        return "Responds when a message contains 'hello bot'."
```

The returned dictionary should contain:

- `message`: response text.
- `attachments`: a list of base64-encoded files. Use an empty list when there are no attachments.

## HashtagHandler contract

A `HashtagHandler` subclass typically implements:

```python
from handlers.hashtag_handler import HashtagHandler


class EchoHandler(HashtagHandler):
    is_intermediate = False

    def get_hashtag(self) -> str:
        return r"#echo"

    def get_substring_mapping(self) -> dict:
        return {0: ("mode", "normal")}

    def get_message(self) -> str:
        if self.hashtag_data.get("mode") == "help":
            return self.get_help_text()
        return self.cleaned_input

    def get_attachments(self) -> list:
        return []

    @staticmethod
    def get_name() -> str:
        return "Echo Handler"

    @staticmethod
    def get_help_text() -> str:
        return "Usage: #echo[.mode] text to echo back."
```

### Dot substrings

`get_substring_mapping()` maps dot-argument positions to a data key and default. For example:

```python
return {0: ("model", "gpt-4.1")}
```

For a message like:

```text
#gpt.gpt-4.1 summarize this
```

The handler can read:

- `self.hashtag_data["model"] == "gpt-4.1"`
- `self.cleaned_input == "summarize this"`

## Help output

When a user sends `#help`, `run.py` loads all handlers with `BaseHandler.get_all_handlers()` and calls each handler's:

- `get_name()`
- `get_help_text()`

Keep help text short enough to fit comfortably in one Signal reply.

## Registration

Most handlers do not need a registry entry. To make a handler discoverable:

1. Add a `.py` file under `handlers/`.
2. Define a class that subclasses `BaseHandler` or `HashtagHandler`.
3. Set `is_intermediate = False`, or omit the attribute.
4. Implement `can_handle()` or `get_hashtag()` as appropriate.
5. Implement help text.

Classes with `is_intermediate = True` are skipped by dynamic discovery. This is useful for abstract helper classes.

## Testing a handler

Use the existing unittest structure:

- `tests/TurboTestCase.py`: shared bot test harness.
- `tests/test_run.py`: examples of top-level command and handler tests.
- `tests/test_mmw.py`: hashtag command test examples.
- `tests/test_asteroid.py`: external API handler example.
- `tests/test_ytdlp.py`: media-download handler examples.

Prefer mocking network calls in new tests unless the test is intentionally integration-style.
