"""User settings: what they are, which values are allowed, and how they are stored.

The API keys are part of the settings while the app runs, but they are kept in
the system's credential store (see keychain.py), never in the settings file.
"""

import json
import os
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path

from .keychain import KeyStore

LANGUAGES = {
    "it": "Italian",
    "es": "Spanish",
    "fr": "French",
    "pt": "Portuguese",
    "en": "English",
    "de": "German",
}

MODELS = {
    "claude-opus-5-5": "Claude Opus 5.5 (best corrections)",
    "claude-sonnet-5-5": "Claude Sonnet 5.5 (faster, half the price)",
}

# Provider id -> (settings field with its key, environment variable used as fallback).
PROVIDER_KEYS = {
    "anthropic": ("api_key", "ANTHROPIC_API_KEY"),
    "openrouter": ("openrouter_api_key", "OPENROUTER_API_KEY"),
}
SECRET_FIELDS = {field for field, _ in PROVIDER_KEYS.values()}


@dataclass(frozen=True)
class Settings:
    provider: str = "anthropic"
    api_key: str = ""
    model: str = "claude-opus-5-5"
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-sonnet-5.5"
    target_language: str = "it"
    voice: str = "it-IT-IsabellaNeural"
    speech_rate: str = "+0%"
    auto_speak: bool = True
    level: str = "A2"
    strictness: str = "lenient"

    @property
    def target_language_name(self) -> str:
        return LANGUAGES[self.target_language]

    def for_conversation(self, target_language: str | None, level: str | None) -> "Settings":
        """These settings, with the language and level a conversation was started in.

        A conversation keeps both for as long as it lives, whatever Settings say
        later. Values that are not given stay as they are. Raises ValueError for
        a value that is not allowed.
        """
        own = {"target_language": target_language, "level": level}
        return replace(self, **{name: _checked(name, value) for name, value in own.items() if value})

    def key_for(self, provider: str) -> str:
        """The API key for a provider: the one from the key store, else the environment variable."""
        field, variable = PROVIDER_KEYS[provider]
        return getattr(self, field) or os.environ.get(variable, "")

    def public(self) -> dict:
        """The settings as the page may see them: without the keys themselves."""
        view = {k: v for k, v in asdict(self).items() if k not in SECRET_FIELDS}
        for provider in PROVIDER_KEYS:
            view[f"has_{provider}_key"] = bool(self.key_for(provider))
        view["has_key"] = view[f"has_{self.provider}_key"]
        return view


DEFAULTS = Settings()
FIELDS = {field.name for field in fields(Settings)}

CHOICES = {
    "provider": set(PROVIDER_KEYS),
    "model": set(MODELS),
    "target_language": set(LANGUAGES),
    "speech_rate": {"-30%", "-15%", "+0%"},
    "level": {"A1", "A2", "B1", "B2"},
    "strictness": {"lenient", "strict"},
}


def _checked(name: str, value: object) -> str | bool:
    """The value as it may be stored, or ValueError if it is not acceptable."""
    if isinstance(getattr(DEFAULTS, name), bool):
        if not isinstance(value, bool):
            raise ValueError(f"Invalid value for {name}")
        return value
    if not isinstance(value, str):
        raise ValueError(f"Invalid value for {name}")
    value = value.strip()
    if name in CHOICES and value not in CHOICES[name]:
        raise ValueError(f"Invalid value for {name}: {value!r}")
    return value


class SettingsStore:
    """Reads and writes the settings: a JSON file, and the key store for the API keys."""

    def __init__(self, file: Path, keys: KeyStore):
        self._file = file
        self._keys = keys

    def _read_file(self) -> dict:
        try:
            stored = json.loads(self._file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return stored if isinstance(stored, dict) else {}

    def _write_file(self, settings: Settings) -> None:
        public = {k: v for k, v in asdict(settings).items() if k not in SECRET_FIELDS}
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps(public, indent=2), encoding="utf-8")

    @staticmethod
    def _plaintext_keys(stored: dict) -> dict[str, str]:
        """Keys that an earlier version wrote into the settings file."""
        return {
            name: stored[name].strip()
            for name in SECRET_FIELDS
            if isinstance(stored.get(name), str) and stored[name].strip()
        }

    def load(self) -> Settings:
        """The stored settings. Missing or unusable entries fall back to the defaults."""
        stored = self._read_file()
        usable = {}
        for name, value in stored.items():
            if name in FIELDS and name not in SECRET_FIELDS:
                try:
                    usable[name] = _checked(name, value)
                except ValueError:
                    pass
        # A key still found in the file is used until it has been moved.
        plaintext = self._plaintext_keys(stored)
        for name in SECRET_FIELDS:
            usable[name] = self._keys.get(name) or plaintext.get(name, "")
        return replace(DEFAULTS, **usable)

    def save(self, changes: dict) -> Settings:
        """Merge validated changes into the stored settings and return the result.

        Unknown names are ignored. Raises ValueError for a value that is not
        allowed, and KeyStoreError if a key cannot be put into the key store.
        """
        accepted = {}
        for name, value in changes.items():
            if name not in FIELDS:
                continue
            value = _checked(name, value)
            # An empty key field means "keep the stored key".
            if name in SECRET_FIELDS and not value:
                continue
            accepted[name] = value
        # The file is rewritten without keys below, so none may be left only there.
        for name, value in self._plaintext_keys(self._read_file()).items():
            if name not in accepted and not self._keys.get(name):
                self._keys.set(name, value)
        for name in SECRET_FIELDS & accepted.keys():
            self._keys.set(name, accepted[name])
        settings = replace(self.load(), **accepted)
        self._write_file(settings)
        return settings

    def move_plaintext_keys(self) -> None:
        """Move keys from the settings file of an earlier version into the key store.

        Raises KeyStoreError if the key store refuses; the file then stays as it is.
        """
        if self._plaintext_keys(self._read_file()):
            self.save({})
