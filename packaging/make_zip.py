"""Builds the download package: a zip with what is needed to run the app.

Run from the repository root: python packaging/make_zip.py [output folder]
Writes Plauderbaum_<version>.zip (default folder: dist/) and prints its path.
"""

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tutor import __version__  # noqa: E402  (needs the path set above)

# What a user needs. Tests, CI, screenshots and this folder stay out.
FOLDERS = ["tutor", "web", "assets", "tools"]
FILES = ["run.bat", "requirements.txt", "LICENSE"]
README = Path(__file__).parent / "readme.txt"


def make_zip(output: Path) -> Path:
    """Write the package into the folder `output` and return the zip's path."""
    name = f"Plauderbaum_{__version__}"
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{name}.zip"
    members = [ROOT / file for file in FILES]
    for folder in FOLDERS:
        members += sorted(
            path for path in (ROOT / folder).rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as package:
        # Everything sits in one versioned folder, so unpacking never scatters files.
        for path in members:
            package.write(path, f"{name}/{path.relative_to(ROOT).as_posix()}")
        package.writestr(f"{name}/readme.txt", README.read_text(encoding="utf-8").replace("{version}", __version__))
    return target


if __name__ == "__main__":
    print(make_zip(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist"))
