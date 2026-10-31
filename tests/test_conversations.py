import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from tutor.conversations import VERSION, ConversationStore, upgraded
from tutor.errors import TutorError
from tutor.models import Node

FIRST = "11111111-1111-1111-1111-111111111111"
SECOND = "22222222-2222-2222-2222-222222222222"


def conversation(title: str, lines: int = 1) -> dict:
    return {
        "title": title,
        "target_language": "it",
        "nodes": [{"id": f"n{i + 1}", "text": "Buongiorno!"} for i in range(lines)],
    }


def valid(**changes) -> dict:
    return {
        "title": "Bar",
        "scenario": {"title": "Bar", "brief": ""},
        "situation": "",
        "target_language": "it",
        "created": "2026-10-31T00:00:00Z",
        "nodes": [{"id": "n1", "role": "tutor", "text": "Buongiorno!"}],
        "active": "n1",
        **changes,
    }


class UpgradeTest(unittest.TestCase):
    def test_a_file_from_before_versions_opens_in_the_current_format(self):
        self.assertEqual(upgraded(valid())["version"], VERSION)

    def test_upgrades_run_step_by_step_from_the_version_of_the_file(self):
        steps = {0: lambda c: {**c, "title": c["title"] + " 1"}, 1: lambda c: {**c, "title": c["title"] + " 2"}}
        with mock.patch("tutor.conversations.VERSION", 2), mock.patch("tutor.conversations.UPGRADES", steps):
            self.assertEqual(upgraded(valid())["title"], "Bar 1 2")
            self.assertEqual(upgraded(valid(version=1))["title"], "Bar 2")

    def test_a_file_from_a_newer_app_is_refused(self):
        with self.assertRaisesRegex(TutorError, "newer version"):
            upgraded(valid(version=VERSION + 1))

    def test_a_damaged_file_gets_a_clear_message(self):
        damaged = [
            valid(nodes=[]),
            valid(nodes="many"),
            valid(version="one"),
            valid(version=-1),
            valid(nodes=[{"id": "n1", "parent": "gone", "role": "tutor", "text": "Ciao"}]),
            {"title": "only a title"},
        ]
        for conversation in damaged:
            with self.subTest(conversation), self.assertRaisesRegex(TutorError, "damaged"):
                upgraded(conversation)


class ConversationStoreTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name) / "conversations"
        self.store = ConversationStore(self.folder)

    def test_every_save_writes_the_version(self):
        self.assertEqual(self.store.save(FIRST, conversation("Bar"))["version"], VERSION)
        self.assertEqual(self.store.load(FIRST)["version"], VERSION)

    def test_empty_before_anything_is_saved(self):
        self.assertEqual(self.store.list_all(), [])
        self.assertIsNone(self.store.load(FIRST))

    def test_save_and_load(self):
        saved = self.store.save(FIRST, conversation("Café", lines=3))
        self.assertEqual(saved["id"], FIRST)
        self.assertTrue(saved["updated"])
        self.assertEqual(self.store.load(FIRST), saved)

    def test_the_id_in_the_document_cannot_differ_from_the_file(self):
        saved = self.store.save(FIRST, {**conversation("Bakery"), "id": "something-else"})
        self.assertEqual(saved["id"], FIRST)

    def test_list_is_newest_first_with_line_counts(self):
        self.store.save(FIRST, conversation("Bakery", lines=3))
        time.sleep(0.01)
        self.store.save(SECOND, conversation("Hotel", lines=5))
        self.assertEqual(
            [(c["id"], c["title"], c["lines"]) for c in self.store.list_all()],
            [(SECOND, "Hotel", 5), (FIRST, "Bakery", 3)],
        )
        time.sleep(0.01)
        self.store.save(FIRST, conversation("Bakery", lines=4))
        self.assertEqual([c["id"] for c in self.store.list_all()], [FIRST, SECOND])

    def test_saving_leaves_no_temporary_file(self):
        self.store.save(FIRST, conversation("Bakery"))
        self.assertEqual([p.name for p in self.folder.iterdir()], [f"{FIRST}.json"])

    def test_delete(self):
        self.store.save(FIRST, conversation("Bakery"))
        self.store.delete(FIRST)
        self.store.delete(FIRST)  # deleting what is gone is not an error
        self.assertEqual(self.store.list_all(), [])

    def test_broken_files_are_skipped(self):
        self.store.save(FIRST, conversation("Bakery"))
        (self.folder / f"{SECOND}.json").write_text("{half a tree", encoding="utf-8")
        self.assertEqual([c["id"] for c in self.store.list_all()], [FIRST])
        self.assertIsNone(self.store.load(SECOND))


if __name__ == "__main__":
    unittest.main()


class NodeTest(unittest.TestCase):
    def test_a_learner_line_keeps_its_failed_attempts(self):
        node = Node(id="n2", parent="n1", role="learner", text="Un pane.", typed="Uno pane.", retries=2)
        self.assertEqual(node.model_dump()["retries"], 2)
        self.assertEqual(Node(id="n1", role="tutor", text="Ciao").retries, 0)
