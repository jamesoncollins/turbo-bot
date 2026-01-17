import random
from typing import Dict


def coin_flip() -> str:
    return random.choice(["heads", "tails"])


TOOL_SPEC: Dict = {
    "type": "function",
    "name": "coin_flip",
    "function": {
        "name": "coin_flip",
        "description": "Flip a fair coin and return heads or tails.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

TOOL_FN = coin_flip
