"""Saved conversations, one JSON file each.

A conversation is a tree of lines: rewinding and answering differently adds a
branch instead of replacing what was there. The browser owns the tree and sends
the whole document after every change; this module only stores it.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from .errors import TutorError
from .models import Conversation

VERSION = 1
# Step n turns a file of version n into version n + 1. Files from before there
# were versions count as 0; they already have the shape of version 1.
UPGRADES = {0: lambda conversation: conversation}


def upgraded(conversation: dict) -> dict:
    """A loaded file in the current format, or TutorError if it cannot be opened."""
    version = conversation.get("version", 0)
    if isinstance(version, int) and version > VERSION:
        raise TutorError("This conversation was saved by a newer version of the app. Update the app to open it.")
    try:
        for step in range(version, VERSION):
            conversation = UPGRADES[step](conversation)
        Conversation.model_validate(conversation)
    except (TypeError, KeyError, ValidationError):
        raise TutorError("This conversation file is damaged and cannot be opened.")
    return {**conversation, "version": VERSION}


class ConversationStore:
    """Keeps conversations as `<id>.json` in one folder."""

    def __init__(self, folder: Path):
        self._folder = folder

    def _file(self, conversation_id: str) -> Path:
        return self._folder / f"{conversation_id}.json"

    @staticmethod
    def _read(path: Path) -> dict | None:
        try:
            conversation = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return conversation if isinstance(conversation, dict) else None

    def list_all(self) -> list[dict]:
        """Summaries of all saved conversations, most recently used first."""
        found = [c for c in map(self._read, self._folder.glob("*.json")) if c]
        found.sort(key=lambda c: c.get("updated", ""), reverse=True)
        return [
            {
                "id": c.get("id", ""),
                "title": c.get("title", ""),
                "target_language": c.get("target_language", ""),
                "updated": c.get("updated", ""),
                "lines": len(c.get("nodes", [])),
            }
            for c in found
        ]

    def load(self, conversation_id: str) -> dict | None:
        return self._read(self._file(conversation_id))

    def save(self, conversation_id: str, conversation: dict) -> dict:
        """Store the conversation under this id and return it as stored."""
        conversation = {
            **conversation,
            "id": conversation_id,
            "version": VERSION,
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        self._folder.mkdir(parents=True, exist_ok=True)
        # Write to a temporary file first so a crash never leaves half a tree behind.
        temporary = self._file(conversation_id).with_suffix(".tmp")
        temporary.write_text(json.dumps(conversation, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(temporary, self._file(conversation_id))
        return conversation

    def delete(self, conversation_id: str) -> None:
        self._file(conversation_id).unlink(missing_ok=True)
