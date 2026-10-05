"""Opens the app in its own window, using an installed Edge or Chrome."""

import os
import subprocess
import webbrowser
from pathlib import Path


def _find_app_browser() -> Path | None:
    candidates = [
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    return next((p for p in candidates if p.is_file()), None)


def open_window(url: str, profile: Path) -> subprocess.Popen | None:
    """Open the app in its own window. Returns the browser process if we own it.

    Without Edge or Chrome the page opens as a tab in the default browser, and
    there is no process to wait for.
    """
    browser = _find_app_browser()
    if browser is None:
        webbrowser.open(url)
        return None
    # A dedicated profile makes the browser a separate process that lives exactly
    # as long as the app window, so the server can stop when the window closes.
    return subprocess.Popen([
        str(browser), f"--app={url}", f"--user-data-dir={profile}",
        "--no-first-run", "--no-default-browser-check", "--window-size=980,860",
    ])
