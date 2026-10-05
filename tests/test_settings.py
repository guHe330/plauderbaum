import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tutor.settings import DEFAULTS, Settings, SettingsStore


class SettingsStoreTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.file = Path(folder.name) / "nested" / "settings.json"
        self.store = SettingsStore(self.file)

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
        self.store.save({"api_key": " sk-ant-1 ", "openrouter_api_key": "sk-or-1"})
        saved = self.store.save({"api_key": "", "openrouter_api_key": "  "})
        self.assertEqual((saved.api_key, saved.openrouter_api_key), ("sk-ant-1", "sk-or-1"))

    def test_unusable_stored_entries_fall_back_to_defaults(self):
        self.file.parent.mkdir(parents=True)
        self.file.write_text(json.dumps({"level": "Z9", "strictness": "strict", "old_setting": 1}), encoding="utf-8")
        loaded = self.store.load()
        self.assertEqual((loaded.level, loaded.strictness), (DEFAULTS.level, "strict"))

    def test_broken_file_gives_defaults(self):
        self.file.parent.mkdir(parents=True)
        self.file.write_text("{not json", encoding="utf-8")
        self.assertEqual(self.store.load(), DEFAULTS)


class SettingsTest(unittest.TestCase):
    def test_public_view_never_contains_keys(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            view = Settings(api_key="sk-ant-secret", openrouter_api_key="sk-or-secret").public()
        self.assertNotIn("sk-ant-secret", json.dumps(view))
        self.assertNotIn("sk-or-secret", json.dumps(view))
        self.assertTrue(view["has_anthropic_key"] and view["has_openrouter_key"] and view["has_key"])

    def test_has_key_follows_the_chosen_provider(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            view = Settings(provider="openrouter", api_key="sk-ant-1").public()
        self.assertTrue(view["has_anthropic_key"])
        self.assertFalse(view["has_key"])

    def test_environment_variable_is_the_fallback_key(self):
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "from-env"}, clear=True):
            self.assertEqual(Settings().key_for("openrouter"), "from-env")
            self.assertEqual(Settings(openrouter_api_key="saved").key_for("openrouter"), "saved")
            self.assertEqual(Settings().key_for("anthropic"), "")

    def test_target_language_name(self):
        self.assertEqual(Settings(target_language="fr").target_language_name, "French")


if __name__ == "__main__":
    unittest.main()
