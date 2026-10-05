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

- Keep interface texts, comments and documentation in English.
- New Python packages go into `requirements.in`, and `requirements.txt` is regenerated from it with hashes (see the comment at the top of `requirements.in`).
- Do not include API keys, saved conversations or anything else from your own data folder.

Security problems are reported privately, see [SECURITY.md](SECURITY.md).
