"""The model call: one prompt in, one JSON object out.

Each provider module offers `complete(settings, system, user, schema) -> str`,
the model's raw answer. `ask` picks the provider chosen in Settings and checks
the answer.
"""

from ..settings import Settings
from . import claude, openrouter
from .answer import parse_answer

PROVIDERS = {
    "anthropic": claude.complete,
    "openrouter": openrouter.complete,
}


def ask(settings: Settings, system: str, user: str, schema: dict) -> dict:
    """Send one prompt and return the answer as a dict that matches `schema`.

    Raises TutorError with a message for the learner if that does not work out.
    """
    complete = PROVIDERS[settings.provider]
    return parse_answer(complete(settings, system, user, schema), schema)
