import json
import tempfile
import unittest
from pathlib import Path

import keyring
from keyring.backend import KeyringBackend
from keyring.errors import PasswordSetError

from tutor.keychain import KeyStoreError, MemoryKeyStore, SystemKeyStore
from tutor.settings import SettingsStore


class RefusingKeyStore(MemoryKeyStore):
    def set(self, name: str, value: str) -> None:
        raise KeyStoreError("The credential store is locked.")


class FakeBackend(KeyringBackend):
    """Stands in for the operating system's credential store."""

    priority = 1

    def __init__(self, broken: bool = False):
        super().__init__()
        self.passwords: dict[tuple[str, str], str] = {}
        self.broken = broken

    def get_password(self, service, username):
        return self.passwords.get((service, username))

    def set_password(self, service, username, password):
        if self.broken:
            raise PasswordSetError("no access")
        self.passwords[(service, username)] = password

    def delete_password(self, service, username):
        del self.passwords[(service, username)]


class KeysInSettingsTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.file = Path(folder.name) / "settings.json"
        self.keys = MemoryKeyStore()
        self.store = SettingsStore(self.file, self.keys)

    def file_content(self) -> dict:
        return json.loads(self.file.read_text(encoding="utf-8"))

    def write_old_file(self, **content):
        self.file.write_text(json.dumps(content), encoding="utf-8")

    def test_saved_keys_go_to_the_key_store_and_not_into_the_file(self):
        saved = self.store.save({"api_key": "sk-ant-1", "openrouter_api_key": "sk-or-1", "level": "B1"})
        self.assertEqual((saved.api_key, saved.openrouter_api_key), ("sk-ant-1", "sk-or-1"))
        self.assertEqual(self.keys.get("api_key"), "sk-ant-1")
        self.assertEqual(self.keys.get("openrouter_api_key"), "sk-or-1")
        self.assertNotIn("sk-", self.file.read_text(encoding="utf-8"))
        self.assertNotIn("api_key", self.file_content())
        self.assertEqual(self.file_content()["level"], "B1")

    def test_keys_come_back_from_the_key_store(self):
        self.store.save({"api_key": "sk-ant-1"})
        again = SettingsStore(self.file, self.keys).load()
        self.assertEqual(again.api_key, "sk-ant-1")
        self.assertEqual(SettingsStore(self.file, MemoryKeyStore()).load().api_key, "")

    def test_a_key_left_in_an_old_file_still_works(self):
        self.write_old_file(api_key="sk-ant-old", level="B1")
        loaded = self.store.load()
        self.assertEqual((loaded.api_key, loaded.level), ("sk-ant-old", "B1"))

    def test_old_plaintext_keys_are_moved(self):
        self.write_old_file(api_key="sk-ant-old", openrouter_api_key="sk-or-old", level="B1")
        self.store.move_plaintext_keys()
        self.assertEqual(self.keys.get("api_key"), "sk-ant-old")
        self.assertEqual(self.keys.get("openrouter_api_key"), "sk-or-old")
        self.assertEqual(self.file_content().get("level"), "B1")
        self.assertNotIn("sk-", self.file.read_text(encoding="utf-8"))
        self.assertEqual(self.store.load().api_key, "sk-ant-old")

    def test_moving_does_not_touch_a_file_without_keys(self):
        self.write_old_file(level="B1", old_setting=1)
        before = self.file.read_text(encoding="utf-8")
        self.store.move_plaintext_keys()
        self.assertEqual(self.file.read_text(encoding="utf-8"), before)

    def test_saving_something_else_does_not_lose_an_old_plaintext_key(self):
        self.write_old_file(api_key="sk-ant-old", openrouter_api_key="sk-or-old")
        saved = self.store.save({"level": "B2", "api_key": "sk-ant-new"})
        self.assertEqual((saved.api_key, saved.openrouter_api_key), ("sk-ant-new", "sk-or-old"))
        self.assertEqual(self.keys.get("openrouter_api_key"), "sk-or-old")
        self.assertNotIn("sk-", self.file.read_text(encoding="utf-8"))

    def test_the_key_store_wins_over_an_old_file(self):
        self.keys.set("api_key", "sk-ant-store")
        self.write_old_file(api_key="sk-ant-old")
        self.assertEqual(self.store.load().api_key, "sk-ant-store")
        self.store.move_plaintext_keys()
        self.assertEqual(self.keys.get("api_key"), "sk-ant-store")

    def test_a_refusing_key_store_leaves_the_file_alone(self):
        store = SettingsStore(self.file, RefusingKeyStore())
        with self.assertRaises(KeyStoreError):
            store.save({"api_key": "sk-ant-1", "level": "B1"})
        self.assertFalse(self.file.exists())

        self.write_old_file(api_key="sk-ant-old")
        before = self.file.read_text(encoding="utf-8")
        with self.assertRaises(KeyStoreError):
            store.move_plaintext_keys()
        self.assertEqual(self.file.read_text(encoding="utf-8"), before)
        self.assertEqual(store.load().api_key, "sk-ant-old")


class SystemKeyStoreTest(unittest.TestCase):
    def use(self, backend: FakeBackend) -> FakeBackend:
        previous = keyring.get_keyring()
        self.addCleanup(keyring.set_keyring, previous)
        keyring.set_keyring(backend)
        return backend

    def test_round_trip_under_the_service_name(self):
        backend = self.use(FakeBackend())
        store = SystemKeyStore("Plauderbaum-test")
        self.assertEqual(store.get("api_key"), "")
        store.set("api_key", "sk-ant-1")
        self.assertEqual(store.get("api_key"), "sk-ant-1")
        self.assertEqual(backend.passwords, {("Plauderbaum-test", "api_key"): "sk-ant-1"})

    def test_a_failing_store_is_reported_in_plain_words(self):
        self.use(FakeBackend(broken=True))
        with self.assertRaisesRegex(KeyStoreError, "environment variable"):
            SystemKeyStore("Plauderbaum-test").set("api_key", "sk-ant-1")


if __name__ == "__main__":
    unittest.main()
