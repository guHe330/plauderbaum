"""The data that travels between the page, the server and the saved files."""

from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["tutor", "learner"]


class Scenario(BaseModel):
    """What the role-play is about and who the tutor plays."""

    title: str = Field(min_length=1, max_length=80)
    brief: str = Field(max_length=500)


class Line(BaseModel):
    """One line of a conversation as the model gets to see it."""

    role: Role
    text: str = Field(max_length=2000)


class StartRequest(BaseModel):
    scenario: Scenario


class ConversationRequest(BaseModel):
    """A model call for an existing conversation.

    The page sends the language and level the conversation was started in;
    without them the current settings apply.
    """

    scenario: Scenario
    situation: str = Field(max_length=1000)
    path: list[Line]
    target_language: str | None = Field(default=None, max_length=10)
    level: str | None = Field(default=None, max_length=10)


class TurnRequest(ConversationRequest):
    text: str = Field(min_length=1, max_length=1000)


class ReplyRequest(ConversationRequest):
    existing: list[str] = Field(min_length=1)


class Node(BaseModel):
    """One line in a saved conversation tree."""

    id: str = Field(min_length=1, max_length=20)
    parent: str | None = Field(default=None, max_length=20)
    role: Role
    # For a learner line: the corrected form. `typed` is what they wrote.
    text: str = Field(max_length=2000)
    translation: str = Field(default="", max_length=2000)
    typed: str = Field(default="", max_length=1000)
    note: str = Field(default="", max_length=4000)
    # A tutor line that closes the scene.
    done: bool = False
    # The child that was shown last, so that switching back to this branch
    # continues where the learner left it.
    pick: str | None = Field(default=None, max_length=20)


class Conversation(BaseModel):
    """A saved conversation: a tree of lines and the line it currently ends on."""

    title: str = Field(min_length=1, max_length=80)
    scenario: Scenario
    situation: str = Field(max_length=1000)
    target_language: str = Field(max_length=10)
    # The level and the voice it was started with. Empty in files from before
    # these were recorded.
    level: str = Field(default="", max_length=10)
    voice: str = Field(default="", max_length=80)
    created: str = Field(max_length=40)
    nodes: list[Node] = Field(min_length=1)
    active: str = Field(max_length=20)
