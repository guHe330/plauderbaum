"""A model on this computer, served by Ollama or LM Studio through their OpenAI-compatible API."""

import json
import urllib.request

from ..errors import TutorError
from ..settings import Settings
from .openrouter import chat


def complete(settings: Settings, system: str, user: str, schema: dict) -> str:
    if not settings.local_model:
        raise TutorError("Choose a local model in Settings.")
    try:
        return chat(f"{settings.local_server}/v1", {}, settings.local_model, system, user, schema, "Local server")
    except OSError:
        raise TutorError(f"Could not reach {settings.local_server}. Is Ollama or LM Studio running?")


def models(server: str) -> list[dict]:
    """The models a local server offers, as {id, label}.

    Raises OSError or ValueError if the list cannot be loaded.
    """
    with urllib.request.urlopen(f"{server}/v1/models", timeout=10) as response:
        data = json.load(response)["data"]
    return sorted(({"id": m["id"], "label": m["id"]} for m in data), key=lambda m: m["id"])
