"""A model on this computer, served by Ollama or LM Studio through their OpenAI-compatible API."""

import json
import urllib.error
import urllib.request

from ..errors import TutorError
from ..settings import Settings
from .openrouter import chat


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"} if token else {}


def complete(settings: Settings, system: str, user: str, schema: dict) -> str:
    if not settings.local_model:
        raise TutorError("Choose a local model in Settings.")
    try:
        return chat(f"{settings.local_server}/v1", _auth(settings.local_token), settings.local_model, system, user, schema, "Local server")
    except OSError:
        raise TutorError(f"Could not reach {settings.local_server}. Is Ollama or LM Studio running?")


def models(server: str, token: str = "") -> list[dict]:
    """The models a local server offers, as {id, label}.

    Raises TutorError if the server refuses the token, or the lack of one, and
    OSError or ValueError if the list cannot be loaded for another reason.
    """
    request = urllib.request.Request(f"{server}/v1/models", headers=_auth(token))
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.load(response)["data"]
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise TutorError("The server wants an API token, or refused this one. Check it in Settings.")
        raise
    return sorted(({"id": m["id"], "label": m["id"]} for m in data), key=lambda m: m["id"])
