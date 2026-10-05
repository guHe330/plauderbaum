# Security Policy

Plauderbaum runs on your own computer, keeps your API keys in your system's credential store and sends your conversation to an AI provider. That is a small attack surface, but it deserves a clear description and a way to report problems.

## Supported versions

Only the latest release is maintained. There are no backports.

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report privately via [GitHub Security Advisories](https://github.com/guHe330/plauderbaum/security/advisories/new) ("Report a vulnerability" on the repository's Security tab).

What to expect:

- This is a one-person spare-time project whose code is written by an AI agent: response is **best effort**, typically within a couple of weeks.
- There is **no bug bounty**.
- Confirmed vulnerabilities are fixed in the next release, with credit in the release notes unless you prefer otherwise.

## How the app is built, as far as it matters for security

- **Local server without login.** The app serves its page and API on `127.0.0.1:8765` only. There is no authentication, so any program running under your user account can call it while the app is open, including the endpoints that spend your API credit.
- **API keys in the credential store.** The keys are kept in the operating system's credential store (Windows Credential Manager), not in a file. That protects them from being read off the disk or copied along with the settings folder, but not from other programs running under your user account, which can ask the credential store for them. The server never sends a stored key back to the page; the page only learns whether one is saved.
- **What leaves the computer.** Conversations go to Anthropic or OpenRouter, the lines that are read aloud go to Microsoft's text-to-speech service. Nothing else is sent, and there is no telemetry. Details are in the [README](README.md#where-your-data-is).
- **Model output is treated as text.** Answers from the model are checked against a fixed format and are inserted into the page as text, never as HTML.
- **Pinned dependencies.** `requirements.txt` pins every Python package with hashes, and `run.bat` installs with `--require-hashes`. The page uses no third-party JavaScript. GitHub Actions are pinned to full commit hashes.

## Scope

In scope: the code in this repository (`tutor/`, `web/`, `run.bat`, `tools/`) and its CI workflow.

Out of scope: issues that require an already-compromised machine or user account beyond what is described above, the behaviour of the AI models themselves (wrong corrections, odd replies), the third-party services the app talks to, and modified copies of the app.
