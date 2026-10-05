import tempfile
import time
import unittest
from pathlib import Path

from tutor.conversations import ConversationStore

FIRST = "11111111-1111-1111-1111-111111111111"
SECOND = "22222222-2222-2222-2222-222222222222"


def conversation(title: str, lines: int = 1) -> dict:
    return {
        "title": title,
        "target_language": "it",
        "nodes": [{"id": f"n{i + 1}", "text": "Buongiorno!"} for i in range(lines)],
    }


class ConversationStoreTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name) / "conversations"
        self.store = ConversationStore(self.folder)

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
