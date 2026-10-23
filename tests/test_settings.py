import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tutor.keychain import MemoryKeyStore
from tutor.settings import DEFAULTS, Settings, SettingsStore


class SettingsStoreTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.file = Path(folder.name) / "nested" / "settings.json"
        self.keys = MemoryKeyStore()
        self.store = SettingsStore(self.file, self.keys)

    def test_defaults_without_a_file(self):
        self.assertEqual(self.store.load(), DEFAULTS)

    def test_save_merges_and_persists(self):
        self.store.save({"level": "B1"})
        saved = self.store.save({"strictness": "strict", "auto_speak": False})
        self.assertEqual((saved.level, saved.strictness, saved.auto_speak), ("B1", "strict", False))
        self.assertEqual(self.store.load(), saved)

    def test_invalid_choice_is_rejected_and_nothing_is_written(self):
        with self.assertRaises(ValueError):
            self.store.save({"level": "C3"})
        self.assertFalse(self.file.exists())

    def test_wrong_type_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.save({"auto_speak": "yes"})
        with self.assertRaises(ValueError):
            self.store.save({"voice": 7})

    def test_unknown_names_are_ignored(self):
        self.assertEqual(self.store.save({"nonsense": 1}), DEFAULTS)

    def test_empty_key_keeps_the_stored_key(self):
        self.store.save({"cursor_api_key": " cursor_1 ", "api_key": " sk-ant-1 ", "openrouter_api_key": "sk-or-1"})
        saved = self.store.save({"cursor_api_key": "", "api_key": "", "openrouter_api_key": "  "})
        self.assertEqual(
            (saved.cursor_api_key, saved.api_key, saved.openrouter_api_key),
            ("cursor_1", "sk-ant-1", "sk-or-1"),
        )

    def test_unusable_stored_entries_fall_back_to_defaults(self):
        self.file.parent.mkdir(parents=True)
        self.file.write_text(json.dumps({"level": "Z9", "strictness": "strict", "old_setting": 1}), encoding="utf-8")
        loaded = self.store.load()
        self.assertEqual((loaded.level, loaded.strictness), (DEFAULTS.level, "strict"))

    def test_broken_file_gives_defaults(self):
        self.file.parent.mkdir(parents=True)
        self.file.write_text("{not json", encoding="utf-8")
        self.assertEqual(self.store.load(), DEFAULTS)

    def test_a_cursor_model_saved_in_the_claude_field_is_kept(self):
        self.file.parent.mkdir(parents=True)
        self.file.write_text(json.dumps({"provider": "cursor", "model": "auto"}), encoding="utf-8")
        loaded = self.store.load()
        self.assertEqual((loaded.provider, loaded.cursor_model, loaded.model), ("cursor", "auto", DEFAULTS.model))

    def test_a_cursor_key_saved_as_the_only_key_is_claimed(self):
        self.keys.set("api_key", "cursor_saved")
        loaded = self.store.load()
        self.assertEqual(loaded.cursor_api_key, "cursor_saved")
        self.assertEqual(loaded.api_key, "")
        self.assertEqual(self.keys.get("cursor_api_key"), "cursor_saved")

    def test_an_anthropic_key_is_not_claimed_for_cursor(self):
        self.keys.set("api_key", "sk-ant-1")
        loaded = self.store.load()
        self.assertEqual(loaded.api_key, "sk-ant-1")
        self.assertEqual(loaded.cursor_api_key, "")


class SettingsTest(unittest.TestCase):
    def test_public_view_never_contains_keys(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            view = Settings(
                cursor_api_key="cursor_secret", api_key="sk-ant-secret", openrouter_api_key="sk-or-secret",
            ).public()
        self.assertNotIn("cursor_secret", json.dumps(view))
        self.assertNotIn("sk-ant-secret", json.dumps(view))
        self.assertNotIn("sk-or-secret", json.dumps(view))
        self.assertTrue(view["has_cursor_key"] and view["has_anthropic_key"] and view["has_openrouter_key"])
        self.assertTrue(view["has_key"])
        self.assertFalse(Settings().public()["has_key"])

    def test_has_key_follows_the_chosen_provider(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            view = Settings(provider="anthropic", cursor_api_key="cursor_1").public()
        self.assertTrue(view["has_cursor_key"])
        self.assertFalse(view["has_key"])

    def test_environment_variable_is_the_fallback_key(self):
        with mock.patch.dict(os.environ, {
            "CURSOR_API_KEY": "from-env",
            "ANTHROPIC_API_KEY": "ant",
            "OPENROUTER_API_KEY": "router",
        }, clear=True):
            self.assertEqual(Settings().key_for("cursor"), "from-env")
            self.assertEqual(Settings(cursor_api_key="saved").key_for("cursor"), "saved")
            self.assertEqual(Settings().key_for("anthropic"), "ant")
            self.assertEqual(Settings().key_for("openrouter"), "router")
            self.assertTrue(Settings().public()["has_key"])

    def test_a_conversation_keeps_its_own_language_and_level(self):
        current = Settings(target_language="es", level="B2", strictness="strict")
        own = current.for_conversation("it", "A1")
        self.assertEqual((own.target_language, own.level), ("it", "A1"))
        self.assertEqual(own.strictness, "strict")  # everything else stays as set

    def test_a_conversation_without_its_own_values_uses_the_settings(self):
        current = Settings(target_language="es", level="B2")
        self.assertEqual(current.for_conversation(None, None), current)
        self.assertEqual(current.for_conversation("it", "").level, "B2")

    def test_a_conversation_cannot_bring_values_that_are_not_allowed(self):
        with self.assertRaises(ValueError):
            Settings().for_conversation("xx", None)
        with self.assertRaises(ValueError):
            Settings().for_conversation(None, "C3")

    def test_target_language_name(self):
        self.assertEqual(Settings(target_language="fr").target_language_name, "French")


if __name__ == "__main__":
    unittest.main()
