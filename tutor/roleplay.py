"""The role-play: scenarios, prompts and the three things the tutor does.

The app owns the flow (advance or rewind); the model only judges the learner's
message and plays the other person.
"""

from .llm import ask
from .models import Line, Scenario
from .settings import Settings

SCENARIOS = [
    {"id": "bakery", "title": "Bakery", "icon": "🥐",
     "brief": "The learner buys bread and pastries at a bakery. The tutor plays the baker."},
    {"id": "restaurant", "title": "Restaurant", "icon": "🍝",
     "brief": "The learner has dinner at a restaurant: table, ordering, paying. The tutor plays the waiter."},
    {"id": "cafe", "title": "Café", "icon": "☕",
     "brief": "The learner orders coffee and a snack at the counter of a café. The tutor plays the barista."},
    {"id": "market", "title": "Market", "icon": "🍅",
     "brief": "The learner buys fruit, vegetables and cheese at a market stall. The tutor plays the vendor."},
    {"id": "hotel", "title": "Hotel", "icon": "🛎️",
     "brief": "The learner checks in at a hotel and asks about breakfast and the room. The tutor plays the receptionist."},
    {"id": "train", "title": "Train station", "icon": "🚆",
     "brief": "The learner buys a train ticket and asks about platform and departure. The tutor plays the ticket clerk."},
    {"id": "directions", "title": "Directions", "icon": "🧭",
     "brief": "The learner asks a passer-by for the way to a sight in town. The tutor plays the passer-by."},
    {"id": "pharmacy", "title": "Pharmacy", "icon": "💊",
     "brief": "The learner has a cold and asks for something at a pharmacy. The tutor plays the pharmacist."},
]

OPENING_SCHEMA = {
    "type": "object",
    "properties": {
        "situation": {"type": "string"},
        "tutor_line": {"type": "string"},
        "translation": {"type": "string"},
    },
    "required": ["situation", "tutor_line", "translation"],
    "additionalProperties": False,
}

TURN_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["ok", "has_errors", "other_language", "question", "unclear"],
        },
        "ideal": {"type": "string"},
        "alternatives": {"type": "array", "items": {"type": "string"}},
        "explanation": {"type": "string"},
        "tutor_reply": {"type": "string"},
        "tutor_reply_translation": {"type": "string"},
        "conversation_done": {"type": "boolean"},
    },
    "required": [
        "verdict", "ideal", "alternatives", "explanation",
        "tutor_reply", "tutor_reply_translation", "conversation_done",
    ],
    "additionalProperties": False,
}

REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "tutor_reply": {"type": "string"},
        "tutor_reply_translation": {"type": "string"},
        "conversation_done": {"type": "boolean"},
    },
    "required": ["tutor_reply", "tutor_reply_translation", "conversation_done"],
    "additionalProperties": False,
}

STRICTNESS = {
    "lenient": (
        "Be lenient: if a native speaker would understand the message without effort, "
        "the verdict is ok even with small slips (a wrong article, a wrong ending, a typo). "
        "Fix those slips in `ideal` and mention the most useful one in `explanation`."
    ),
    "strict": (
        "Be strict: any error in grammar, word choice or spelling makes the verdict "
        "has_errors, so the learner repeats the sentence correctly."
    ),
}


def _system_prompt(settings: Settings, scenario: Scenario) -> str:
    target = settings.target_language_name
    return f"""You are a patient {target} tutor running a role-play conversation with one learner.

The learner is learning \
{target} at CEFR level {settings.level}. They type their side of the conversation; your \
lines are read aloud by a text-to-speech voice, so write plain sentences without markup, \
emoji or stage directions.

Scenario: {scenario.title}. {scenario.brief}
The learner plays themselves. Stay in your role for every role-play line, keep those lines \
to one or two short sentences at the learner's level, and move the scene forward so that it \
reaches a natural end after roughly six to ten learner turns.

Everything you write for the role-play is in {target}. Explanations and translations are in \
English.

The learner's keyboard may lack the letters of {target}: never treat missing accents or apostrophe variants \
as errors, just write them correctly yourself.

{STRICTNESS[settings.strictness]}"""


TURN_INSTRUCTIONS = """Judge the learner's new message and answer with these fields.

verdict:
- ok: the message is in the target language and acceptable under the strictness rule.
- has_errors: it is in the target language but has errors that matter.
- other_language: it is wholly or partly in another language, usually their native one, because the learner did not \
know how to say it. A mixed sentence counts as other_language.
- question: the learner steps out of the role-play to ask you, the tutor, something about \
the language or the situation.
- unclear: you cannot tell what they mean.

ideal: what the learner should say, in the target language, natural and at their level. It \
expresses what they meant, not what you would prefer them to say. For ok it is their own \
message with small slips fixed, identical if it was already right. For question or unclear \
it is a suggestion for what they could say next, or an empty string if you have none.

alternatives: other natural ways to say the same thing in the target language, different \
from `ideal`. For has_errors and other_language always give at least two, so that the \
learner sees at least three variants together with `ideal`; vary them in a useful way (more \
polite, more casual, shorter). For ok, give none or one.

explanation: brief and specific, in English. For has_errors, say what was \
wrong and why. For other_language, name the key word or structure they were missing and \
nothing else: never mention that they wrote in another language or mixed languages, they \
know. Leave it empty if the variants speak for themselves. For question, answer it. For ok, \
leave it empty unless you fixed a slip or have a short tip.

tutor_reply: only when the verdict is ok, your next role-play line, responding to `ideal`. \
Otherwise an empty string, because the learner will try again first.

tutor_reply_translation: the translation of tutor_reply, or an empty string.

conversation_done: true only when the verdict is ok and your tutor_reply closes the scene."""


def open_conversation(settings: Settings, scenario: Scenario) -> dict:
    """The situation and the tutor's opening line for a new conversation."""
    target = settings.target_language_name
    user = f"""Start a new conversation for this scenario. Invent fresh concrete details \
(place, time of day, what is on offer) so that it differs from run to run.

Answer with these fields.
situation: one or two sentences in English that set the scene for the \
learner and say what they are there to do.
tutor_line: your opening role-play line in {target}.
translation: the translation of tutor_line into English."""
    return ask(settings, _system_prompt(settings, scenario), user, OPENING_SCHEMA)


def _transcript(path: list[Line]) -> str:
    return "\n".join(
        f"{'Tutor' if line.role == 'tutor' else 'Learner'}: {line.text}" for line in path
    )


def other_reply(
    settings: Settings, scenario: Scenario, situation: str, path: list[Line], existing: list[str],
) -> dict:
    """A different tutor line for a point where the learner has already seen `existing`.

    `path` ends with the learner line to respond to, or is empty for the opening line.
    """
    target = settings.target_language_name
    if path:
        context = f"""Conversation so far (the learner's lines are shown in their corrected form):
{_transcript(path)}

Give your next role-play line, responding to the learner's last line."""
    else:
        context = "The conversation has not started yet. Give your opening role-play line."
    seen = "\n".join(f"- {line}" for line in existing)
    user = f"""Situation given to the learner: {situation}

{context}

The learner has already seen the lines below from you at this point and wants to practise \
how else the other person could react. Take the conversation in a noticeably different \
direction (a different question, offer, problem or mood) that is still plausible for the \
scene and the situation:
{seen}

Answer with these fields.
tutor_reply: your line in {target}.
tutor_reply_translation: its translation into English.
conversation_done: true only if this line closes the scene."""
    return ask(settings, _system_prompt(settings, scenario), user, REPLY_SCHEMA)


def judge_turn(settings: Settings, scenario: Scenario, situation: str, path: list[Line], text: str) -> dict:
    """The verdict on the learner's new message and, if it passes, the tutor's next line."""
    user = f"""Situation given to the learner: {situation}

Conversation so far (the learner's lines are shown in their corrected form):
{_transcript(path)}

The learner's new message:
{text}

{TURN_INSTRUCTIONS}"""
    return ask(settings, _system_prompt(settings, scenario), user, TURN_SCHEMA)
