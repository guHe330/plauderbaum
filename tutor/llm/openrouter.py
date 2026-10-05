"""Any model on OpenRouter, through its OpenAI-compatible API."""

import functools
import json
import urllib.error
import urllib.request

from ..errors import TutorError
from ..paths import APP_NAME
from ..settings import Settings

API = "https://openrouter.ai/api/v1"


def complete(settings: Settings, system: str, user: str, schema: dict) -> str:
    api_key = settings.key_for("openrouter")
    if not api_key:
        raise TutorError("No API key yet. Add your OpenRouter API key in Settings.")
    if not settings.openrouter_model:
        raise TutorError("Choose an OpenRouter model in Settings.")
    # Not every model behind OpenRouter enforces response_format, so the schema is
    # also spelled out in the prompt.
    user += (
        "\n\nAnswer with a single JSON object and nothing else. It must match this JSON schema:\n"
        + json.dumps(schema)
    )
    body = {
        "model": settings.openrouter_model,
        "max_tokens": 8000,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "answer", "strict": True, "schema": schema},
        },
    }
    request = urllib.request.Request(
        f"{API}/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": APP_NAME,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read()
    except OSError:
        raise TutorError("Could not reach OpenRouter. Check your internet connection.")
    return read_completion(status, raw)


def read_completion(status: int, raw: bytes) -> str:
    """The model's text from a chat completion response, or TutorError."""
    try:
        data = json.loads(raw)
    except ValueError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    # OpenRouter also reports upstream failures as an error object in a 200 response.
    error = data.get("error")
    if isinstance(error, dict) and isinstance(error.get("code"), int):
        status = error["code"]
    if status == 401:
        raise TutorError("The OpenRouter API key was rejected. Check it in Settings.")
    if status == 402:
        raise TutorError("Your OpenRouter credit is used up.")
    if status == 429:
        raise TutorError("Rate limit reached. Wait a moment and try again.")
    if error or status >= 400:
        message = error.get("message") if isinstance(error, dict) else None
        raise TutorError(f"OpenRouter error ({status}): {message or 'no details given'}")
    choice = (data.get("choices") or [{}])[0]
    if choice.get("finish_reason") == "length":
        raise TutorError("The answer was cut off. Try again.")
    return (choice.get("message") or {}).get("content") or ""


@functools.cache
def structured_output_models() -> tuple[dict, ...]:
    """Models that can return structured output, as {id, label}, to suggest in Settings.

    Fetched once per run. Raises OSError or ValueError if the list cannot be loaded.
    """
    with urllib.request.urlopen(f"{API}/models", timeout=20) as response:
        models = json.load(response)["data"]
    wanted = {"structured_outputs", "response_format"}
    return tuple(sorted(
        ({"id": m["id"], "label": m.get("name", m["id"])}
         for m in models
         if not m.get("supported_parameters") or wanted & set(m["supported_parameters"])),
        key=lambda m: m["id"],
    ))
