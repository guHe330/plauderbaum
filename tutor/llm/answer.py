"""Reads and checks the JSON object a model answered with."""

import json

from ..errors import TutorError

# The answer schemas are flat objects, so one level of type checking is enough.
JSON_TYPES = {"string": str, "boolean": bool, "array": list}


def parse_answer(text: str, schema: dict) -> dict:
    """The model's answer as a dict, or TutorError if it does not match `schema`."""
    unreadable = TutorError("The model returned an unreadable answer. Try again, or pick another model.")
    # Models without structured output support may wrap the JSON in prose or a code fence.
    start, end = text.find("{"), text.rfind("}")
    try:
        answer = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        raise unreadable
    if not isinstance(answer, dict):
        raise unreadable
    for key, spec in schema["properties"].items():
        value = answer.get(key)
        if not isinstance(value, JSON_TYPES[spec["type"]]) or ("enum" in spec and value not in spec["enum"]):
            raise unreadable
    return answer
