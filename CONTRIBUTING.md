# Contributing

Plauderbaum is a personal tool that is shared as it is. Issues and pull requests are welcome, but there is no promise that they will be answered or merged.

## Good to know

- **The code is written by an AI agent.** Changes are made by Claude Code, directed by one person, and reviewed by using the app rather than line by line. A pull request may be reworked by the agent instead of being merged as it is.
- **Things move.** File layout, settings and the format of saved conversations can change between releases.
- **Open an issue first** for anything larger than a small fix, so that work is not done twice or in a direction that will not be merged.

## Licence of contributions

By submitting a contribution you agree that it is licensed under the same terms as the project: the GNU General Public License, version 3 or (at your option) any later version. You keep your copyright. There is no separate contributor agreement to sign.

Only contribute what you have the right to contribute under that licence.

## Before you open a pull request

Run the tests from the app folder:

```
.venv\Scripts\python.exe -m unittest discover -s tests
node --test
```

On macOS the Python command is `.venv/bin/python -m unittest discover -s tests`.

The Python tests cover settings, conversation storage, answer parsing, provider error handling and the prompts, without calling a model. The JavaScript tests cover the conversation tree and need Node.js 22 or newer; the app itself does not need Node.

To start without the starter script: `.venv\Scripts\python.exe -m tutor` on Windows, or `.venv/bin/python -m tutor` on macOS.

- Keep interface texts, comments and documentation in English.
- New Python packages go into `requirements.in`, and `requirements.txt` is regenerated from it with hashes (see the comment at the top of `requirements.in`).
- Do not include API keys, saved conversations or anything else from your own data folder.

## Releases

Versions are numbered `major.minor.patch`. While the major number is 0, any release may change the format of saved conversations or the settings.

The version is written down in one place, `__version__` in `tutor/__init__.py`. To publish a release:

1. Change `__version__` and commit.
2. Tag that commit `v<version>`, for example `v0.1.0`, and push the tag.

The [release workflow](.github/workflows/release.yml) refuses a tag that does not match `__version__`, runs the tests, builds `Plauderbaum_<version>.zip` with `packaging/make_zip.py`, attests where it was built and attaches it to a new GitHub release. To build the same zip locally: `python packaging/make_zip.py`, which writes to `dist/`.

## Security

Security problems are reported privately, see [SECURITY.md](SECURITY.md).
