import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import tutor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packaging"))
from make_zip import make_zip  # noqa: E402  (needs the path set above)


class VersionTest(unittest.TestCase):
    def test_version_is_three_numbers(self):
        # The release workflow compares this with the tag vX.Y.Z.
        self.assertRegex(tutor.__version__, r"^\d+\.\d+\.\d+$")


class PackageTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.zip = make_zip(Path(folder.name))
        with zipfile.ZipFile(self.zip) as package:
            self.names = set(package.namelist())
            self.readme = package.read(f"Plauderbaum_{tutor.__version__}/readme.txt").decode("utf-8")

    def test_name_carries_the_version(self):
        self.assertEqual(self.zip.name, f"Plauderbaum_{tutor.__version__}.zip")

    def test_everything_is_inside_one_versioned_folder(self):
        top = {name.split("/")[0] for name in self.names}
        self.assertEqual(top, {f"Plauderbaum_{tutor.__version__}"})

    def test_contains_what_is_needed_to_run(self):
        root = f"Plauderbaum_{tutor.__version__}"
        for needed in [
            "run.bat", "requirements.txt", "LICENSE", "readme.txt",
            "tutor/__main__.py", "tutor/llm/claude.py", "web/index.html", "web/main.js",
            "assets/icon.png", "tools/make_shortcut.ps1",
        ]:
            self.assertIn(f"{root}/{needed}", self.names)

    def test_leaves_out_what_a_user_does_not_need(self):
        unwanted = re.compile(r"/(tests|docs|packaging|\.github|\.venv|\.git)/|__pycache__|\.pyc$")
        self.assertEqual([name for name in self.names if unwanted.search(name)], [])

    def test_readme_names_the_version(self):
        self.assertIn(f"Plauderbaum {tutor.__version__}", self.readme)
        self.assertNotIn("{version}", self.readme)


if __name__ == "__main__":
    unittest.main()
