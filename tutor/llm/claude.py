"""Claude through the Anthropic API."""

import anthropic

from ..errors import TutorError
from ..settings import Settings


def complete(settings: Settings, system: str, user: str, schema: dict) -> str:
    api_key = settings.key_for("anthropic")
    if not api_key:
        raise TutorError("No API key yet. Add your Anthropic API key in Settings.")
    client = anthropic.Anthropic(api_key=api_key)
    try:
        # fallbacks="default": if a safety classifier declines a request, the API
        # re-runs it on Anthropic's recommended fallback model instead of failing.
        response = client.beta.messages.create(
            model=settings.model,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={
                "effort": "low",
                "format": {"type": "json_schema", "schema": schema},
            },
        )
    except anthropic.AuthenticationError:
        raise TutorError("The API key was rejected. Check it in Settings.")
    except anthropic.PermissionDeniedError as e:
        raise TutorError(f"The API key lacks permission for this request: {e.message}")
    except anthropic.RateLimitError:
        raise TutorError("Rate limit reached. Wait a moment and try again.")
    except anthropic.APIStatusError as e:
        raise TutorError(f"Claude API error ({e.status_code}): {e.message}")
    except anthropic.APIConnectionError:
        raise TutorError("Could not reach the Claude API. Check your internet connection.")

    if response.stop_reason == "refusal":
        raise TutorError("Claude declined to answer this message. Try rephrasing it.")
    if response.stop_reason == "max_tokens":
        raise TutorError("The answer was cut off. Try again.")
    return next((b.text for b in response.content if b.type == "text"), "")
