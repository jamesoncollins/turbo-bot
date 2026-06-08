# Architecture

TurboBot is a Python Signal bot that routes incoming messages through a small handler framework. The runtime entrypoint is `run.py`, and feature code lives mostly in `handlers/`, `utils/`, and `tool_functions/`.

## Runtime overview

`run.py` configures and starts a `SignalBot` instance using environment variables such as `SIGNAL_API_URL` and `BOT_NUMBER`. The bot registers `TurboBotCommand`, whose `handle` method is the main message-processing path.

Every normal bot reply is prefixed with `LOGMSG`, currently:

```text
----TURBOBOT----
```

`TurboBotCommand.handle` reads the raw Signal message, extracts useful metadata, determines whether the message is private or group-based, applies allow/ignore configuration, and then dispatches matching messages to handlers.

## Authorization and routing

Message routing is controlled by environment variables parsed through `utils.misc_utils.parse_env_var`:

- `CONTACT_NUMBERS`: allowed private contacts. Use `true` to allow all, `false`/unset to allow none depending on call site, a single value, or a semicolon-separated list.
- `GROUP_NAMES`: allowed group names. Use `true` to allow all, or a semicolon-separated list of group names.
- `IGNORE_GROUPS`: optional group names that should be ignored even if otherwise allowed.

Group messages are resolved from Signal internal group IDs to group metadata using `find_group_by_internal_id` in `run.py`.

## Built-in command handling

Before dynamic handlers are consulted, `TurboBotCommand.handle` checks a few direct commands and special cases, including:

- `#ping`: health check response.
- Reddit URLs: direct video download/reply path.
- `#status`: machine and git status.
- `#reboot`: exits the bot process so the surrounding launcher can restart it.
- `#branch`: reports the current Git branch, but only when the bot started with `GIT_REPO_BRANCH=devel`.
- `#branch <name>`: on the `devel` bot only, asks the shell wrapper to fetch, check out, hard-reset to `origin/<name>`, and relaunch the bot process in-place.
- `#help`: lists help text from all dynamically discovered handlers.

## Handler discovery

Handlers are discovered by `BaseHandler.get_all_handlers()` in `handlers/base_handler.py`.

Discovery rules:

1. Iterate over Python modules in the `handlers/` directory.
2. Import each module as `handlers.<module_name>`.
3. Inspect classes in the module.
4. Include classes that subclass `BaseHandler`.
5. Exclude `BaseHandler` itself.
6. Exclude classes with `is_intermediate = True`.

Because discovery is dynamic, most new handlers do not need to be registered manually. Put the handler class in `handlers/`, subclass `BaseHandler` or a subclass such as `HashtagHandler`, and make sure it is not marked intermediate.

## Handler execution contract

The base contract is defined by `handlers/base_handler.py`:

- `can_handle(self) -> bool`: return true if the handler should process the current input string.
- `process_message(self, msg, attachments) -> dict`: return a dictionary with:
  - `message`: text to send back to Signal.
  - `attachments`: a list of base64-encoded attachments.
- `get_name() -> str`: a human-readable handler name used by help output.
- `get_help_text() -> str`: help text used by `#help`.

`BaseHandler.process_message` assumes subclass implementations provide `get_message()` and `get_attachments()`. Handlers can override `process_message` when they need custom behavior.

## Hashtag command abstraction

`handlers/hashtag_handler.py` provides `HashtagHandler`, a convenience subclass for commands such as `#gpt`, `#mmw`, `#golf`, and `#asteroid`.

A hashtag handler supplies:

- `get_hashtag()`: the command pattern, such as `r"#gpt"`.
- `get_substring_mapping()`: positional dot-argument names and defaults.

For example, a message like `#gpt.gpt-4.1 explain this` can be split into the command, model substring, and cleaned prompt text.

## GPT tool subsystem

`handlers/gpt_handler.py` implements the `#gpt` command and dynamically loads optional function tools from `tool_functions/`.

Tool modules are ordinary Python files that expose `TOOL_SPEC` and `TOOL_FN`. See `docs/GPT_TOOLS.md` for the tool-authoring contract.

## Important paths

- `run.py`: application entrypoint and message dispatch.
- `handlers/base_handler.py`: common handler base class and dynamic discovery.
- `handlers/hashtag_handler.py`: helper for hashtag/dot-argument command handlers.
- `handlers/gpt_handler.py`: OpenAI-backed GPT and image-generation handler.
- `tool_functions/`: dynamically loaded GPT function tools.
- `utils/`: shared helpers for env parsing, media conversion, Reddit, video scraping, machine info, and git info.
- `tests/`: unittest-based test suite with Signal API mocks.
