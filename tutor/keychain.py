"""Where the API keys are kept: the operating system's credential store.

That is the Windows Credential Manager or the macOS Keychain, reached through
the `keyring` package. The keys never go into the settings file.
"""

from typing import Protocol

import keyring
from keyring.errors import KeyringError

from .paths import APP_NAME


class KeyStoreError(Exception):
    """The credential store could not take a key. The message is fit to show."""


class KeyStore(Protocol):
    def get(self, name: str) -> str:
        """The stored secret, or an empty string if there is none."""

    def set(self, name: str, value: str) -> None:
        """Store the secret. Raises KeyStoreError if that is not possible."""


class SystemKeyStore:
    """The current user's credential store, with this app as the service name."""

    def __init__(self, service: str = APP_NAME):
        self._service = service

    def get(self, name: str) -> str:
        try:
            return keyring.get_password(self._service, name) or ""
        except KeyringError:
            # No usable store on this system: the same as no key saved.
            return ""

    def set(self, name: str, value: str) -> None:
        try:
            keyring.set_password(self._service, name, value)
        except KeyringError as error:
            raise KeyStoreError(
                "Could not save the key in your system's credential store "
                f"({error or type(error).__name__}). You can set it as an environment variable instead."
            )


class MemoryKeyStore:
    """Keeps secrets for the lifetime of the object only. For tests."""

    def __init__(self):
        self._secrets: dict[str, str] = {}

    def get(self, name: str) -> str:
        return self._secrets.get(name, "")

    def set(self, name: str, value: str) -> None:
        self._secrets[name] = value
