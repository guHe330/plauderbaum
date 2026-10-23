"""One tutor turn, answered by a local Cursor agent.

The agent is offered no tools and runs in an empty folder, so a turn cannot
edit this project. It still needs a Cursor API key.
"""

import json

from cursor_sdk import (
    Agent,
    AgentOptions,
    AuthenticationError,
    CursorAgentError,
    LocalAgentOptions,
    NetworkError,
    PermissionDeniedError,
    RateLimitError,
    SandboxOptions,
)

from ..errors import TutorError
from ..paths import cache_folder
from ..settings import Settings


def complete(settings: Settings, system: str, user: str, schema: dict) -> str:
    """The agent's reply text. Raises TutorError with a message for the learner."""
    api_key = settings.key_for("cursor")
    if not api_key:
        raise TutorError("No API key yet. Add your Cursor API key in Settings.")
    # An empty folder, not the program folder: the agent has nothing to change.
    workspace = cache_folder() / "agent-workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    prompt = (
        f"{system}\n\n{user}\n\n"
        "Reply with one JSON object and no other text. "
        "It must match this JSON schema:\n"
        f"{json.dumps(schema)}"
    )
    try:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model=settings.cursor_model,
                tools=[],
                local=LocalAgentOptions(
                    cwd=workspace,
                    sandbox_options=SandboxOptions(enabled=True),
                ),
            ),
        )
    except AuthenticationError:
        raise TutorError("The API key was rejected. Check it in Settings.")
    except PermissionDeniedError as error:
        raise TutorError(f"The API key lacks permission for this request: {error.message}")
    except RateLimitError:
        raise TutorError("Rate limit reached. Wait a moment and try again.")
    except NetworkError:
        raise TutorError("Could not reach Cursor. Check your internet connection.")
    except CursorAgentError as error:
        detail = error.message or type(error).__name__
        raise TutorError(f"The Cursor agent could not start ({detail}).")
    if result.status == "error":
        raise TutorError("The Cursor agent failed to answer. Try again.")
    if result.status == "cancelled":
        raise TutorError("The Cursor agent was cancelled. Try again.")
    return result.result or ""
