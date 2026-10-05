"""Where things live on disk.

The program folder holds only code. Everything personal (settings with the API
keys, saved conversations) is kept in the user's application data folder.
"""

import os
import sys
from pathlib import Path

APP_NAME = "Plauderbaum"

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
ASSETS = ROOT / "assets"


def _user_folder(windows: tuple[str, str], mac: str, other: tuple[str, str]) -> Path:
    """This app's folder below a per-user base folder.

    `windows` and `other` are (environment variable, fallback below the home
    folder); macOS has fixed locations.
    """
    home = Path.home()
    if sys.platform == "darwin":
        return home / mac / APP_NAME
    variable, fallback = windows if sys.platform == "win32" else other
    return Path(os.environ.get(variable) or home / fallback) / APP_NAME


def data_folder() -> Path:
    """Settings and saved conversations: %APPDATA% on Windows."""
    return _user_folder(
        windows=("APPDATA", "AppData/Roaming"),
        mac="Library/Application Support",
        other=("XDG_DATA_HOME", ".local/share"),
    )


def cache_folder() -> Path:
    """Things that can be thrown away, like the browser profile: %LOCALAPPDATA% on Windows."""
    return _user_folder(
        windows=("LOCALAPPDATA", "AppData/Local"),
        mac="Library/Caches",
        other=("XDG_CACHE_HOME", ".cache"),
    )
