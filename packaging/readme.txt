Plauderbaum {version}
====================

Practise everyday conversations in a foreign language with an AI tutor.

To start
--------
1. Install Python 3.12 or newer, if "py --version" in a terminal does not
   already print it: https://www.python.org/downloads/
   or run: winget install Python.Python.3.12
2. Double-click run.bat. The first start takes a minute, because it sets up
   a private Python environment in the folder .venv next to it.
3. Open Settings in the app and add your Anthropic or OpenRouter API key.

For a shortcut with an icon, run in this folder:
   powershell -ExecutionPolicy Bypass -File tools\make_shortcut.ps1

To update
---------
Unpack the new version into a folder of its own and start it there. Your
settings and conversations are kept in %APPDATA%\Plauderbaum, not in this
folder, so the old folder can simply be deleted.

More
----
Full documentation, source code and issue tracker:
https://github.com/guHe330/plauderbaum

Plauderbaum is free software under the GNU General Public License, version 3
or later (see LICENSE). It comes without any warranty.
