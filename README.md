# Plauderbaum

[![CI](https://github.com/guHe330/plauderbaum/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/guHe330/plauderbaum/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/guHe330/plauderbaum)](https://github.com/guHe330/plauderbaum/releases/latest)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Platform: Windows 10 | 11, macOS](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011%2C%20macOS-0078d4.svg)](#what-you-need)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776ab.svg?logo=python&logoColor=white)](#what-you-need)
[![Code: 100% agentic](https://img.shields.io/badge/code-100%25%20agentic-8FD9B6.svg)](CONTRIBUTING.md#good-to-know)

![Plauderbaum: practise everyday conversations in a foreign language with an AI tutor. Answer, get corrected, rewind, branch out.](docs/banner.png)

A small local app for practising everyday conversations in a foreign language. You pick a situation (bakery, hotel, train station, or a topic of your own), an AI model plays the other person, and you type your side. The tutor's lines are read aloud.

- **Every message is corrected.** Each one is judged before the conversation moves on. If it has errors, you see how to say it and try again.
- **Stuck? Answer in your native language.** You get the sentence in the language you are learning, in at least three variants, and then say it yourself.
- **Conversation trees.** Rewind to any point and answer differently, or ask how else the other person could have reacted. Earlier branches are kept, and you can switch between them.
- **Saved automatically.** Conversations survive a restart and can be reopened from the start page.
- **Your own key.** It talks to Claude through the Anthropic API, or to any model on OpenRouter.

![A conversation in a café: the learner's lines with corrections, and a tutor line that has a second version](docs/screenshots/conversation.png)

> **Built entirely by an AI agent.** Every line of code, the tests and this README were written by Claude (Anthropic's coding agent, Claude Code), directed by one person in conversation. No code was written by hand. It was reviewed by using it; nobody has audited it line by line.

> **A personal tool, shared as it is.** It was made for one learner's needs (learning Italian) and is published in case it is useful to someone else. There is no roadmap and no promise of support.

> **Early and moving.** Expect a lot to change: features, file layout, the format of saved conversations. Updates may break things without a migration path.

> **You pay, and you keep the key safe.** The app uses your own API key. Everything it spends is billed to your account, and keeping that key safe is up to you. The app sets no spending limit. See [Cost](#cost) and [Your API key](#your-api-key).

> **It is not offline.** Your conversations are sent to the AI provider you choose, unless you run a model locally with Ollama or LM Studio, and the lines that are read aloud go to Microsoft's voice service. See [What leaves your computer](#what-leaves-your-computer).

## What you need

| | |
|---|---|
| Operating system | Windows 10 or 11, or macOS. On Windows, start with `run.bat`. On macOS, start with `./run.sh`. |
| Python | 3.12 or newer |
| Browser | Microsoft Edge or Google Chrome (Edge is part of Windows) |
| API key | An [Anthropic API key](https://console.anthropic.com/) or an [OpenRouter key](https://openrouter.ai/keys), with some credit on it. Not needed with a local model in [Ollama](https://ollama.com) or [LM Studio](https://lmstudio.ai). |
| Internet | Needed for the model and for the voice |

The API is billed by usage and is separate from a Claude.ai subscription. See [Cost](#cost).

## First start

### 1. Install Python

Skip this if `py --version` in a terminal already prints 3.12 or newer.

- Download the Windows installer from [python.org/downloads](https://www.python.org/downloads/) and run it with the default options, **or**
- run `winget install Python.Python.3.12` in a terminal.

Both install the `py` launcher that `run.bat` uses.

### 2. Get the app

Download `Plauderbaum_<version>.zip` from the [latest release](https://github.com/guHe330/plauderbaum/releases/latest) and unpack it. It contains only what is needed to run the app, in one folder named after the version.

Put the folder wherever you like. Nothing personal is stored in it.

To work on the code, or to get the newest state between releases, clone the repository instead:

```
git clone https://github.com/guHe330/plauderbaum.git
```

### 3. Run it

On Windows, double-click **`run.bat`**. On macOS, run **`./run.sh`** in a terminal from the app folder (Python 3.12 or newer has to be available as `python3`).

The first start takes a minute: it creates a private Python environment in the folder `.venv` and installs the pinned dependencies from `requirements.txt` into it. After an update that changes `requirements.txt`, the next start installs again. Nothing is installed system-wide. After that the app opens in its own window.

If the setup fails, delete the `.venv` folder and start again.

### 4. Add your API key

The app opens with a notice that a key is missing. Go to **Settings**, paste your key, choose the language you are learning and your level, and press **Save**. Then switch back to **Tutor** and pick a situation.

### Optional: a shortcut with an icon

```
powershell -ExecutionPolicy Bypass -File tools\make_shortcut.ps1
```

This creates `Plauderbaum.lnk` in the app folder. Move it to the desktop or pin it to the taskbar.

### Stopping

Close the app window. The local server stops with it.

### Updating

Download the newer zip, unpack it into a folder of its own and start it there. Settings and conversations are kept outside the app folder (see [Where your data is](#where-your-data-is)), so they carry over and the old folder can be deleted. The version you are running is shown at the bottom of the Settings tab.

## Using it

![The start page with eight situations, a field for a topic of your own, and earlier conversations](docs/screenshots/home.png)

1. **Pick a situation** on the start page, or type a topic of your own.
2. **Read or listen** to the other person's line. *Translation* shows what it means, *Listen* plays it again.
3. **Type your answer.**
   - If it is fine, the conversation continues. Small slips are fixed in a note below your message.
   - If it has errors, or you answered in another language, a card shows how to say it, with alternatives. Type it again in the language you are learning.
   - You can also ask the tutor a question about the language at any time.
4. **Branch out.**
   - *↩ Answer from here* on any earlier line rewinds to that point, so you can answer differently.
   - *⟳ Other reply* asks for a different reaction from the other person.
   - Where a turn has several versions, `‹ 2/3 ›` switches between them.
   - The **tree** beside the chat shows every branch; it only indents where the conversation forks, and ▾ folds an alternative away. Click a line to go back to it: at the other person's line (🤖) you can answer differently, at your own line ask for another reply. Typing an answer you already gave there takes you back to that branch. Your lines are marked green when they passed as typed, amber when they passed with a small correction, red when it took more than one attempt; a tick marks a branch that reached the end. *🌳 Tree* folds it away, and its corner drags it wider.
5. **At the end** you get the whole conversation in its corrected form and can play it back in one go.

<img src="docs/screenshots/tree.png" width="304" alt="The tree of a café conversation: the waiter's lines marked with a robot, the learner's with coloured dots, and two forks where a different reply and a different answer were tried">

*← All conversations* and the logo both lead back to the start page. The conversation you leave is already saved and listed there under *Earlier conversations*.

## Settings

![The Settings tab: AI model, learning and voice](docs/screenshots/settings.png)

| Setting | Values | What it does |
|---|---|---|
| Provider | Anthropic, OpenRouter, Local | Where the model call goes. *Local* is a model running on this computer in Ollama or LM Studio. |
| Anthropic API key | | Used when the provider is Anthropic. Leave the field empty to keep the saved key. |
| Model (Anthropic) | Claude Opus 5.5, Claude Sonnet 5.5 | Opus gives the best corrections. Sonnet is faster and cheaper. |
| OpenRouter API key | | Used when the provider is OpenRouter. |
| Model (OpenRouter) | any model id | Suggestions come from OpenRouter's list of models that support structured output. Weaker models give weaker corrections, and some cannot produce the answer format at all. |
| Server (Local) | an address | Where Ollama (`http://localhost:11434`) or LM Studio (`http://localhost:1234`) listens. |
| Model (Local) | the models the server offers | Pull a model in Ollama or load one in LM Studio first. Small local models are noticeably weaker at corrections than Claude, and some break the answer format. |
| I am learning | Italian, Spanish, French, Portuguese, English, German | The language of new conversations. Changing it also reloads the list of voices. |
| My level | A1, A2, B1, B2 | How simple the other person's lines and the suggested sentences are, in new conversations. |
| Corrections | Lenient, Strict | Lenient lets small slips pass with a note. Strict makes you repeat the sentence until it is correct. |
| Tutor voice | voices for the chosen language | *Test* plays a sample. |
| Speed | Normal, Slower, Slow | Speaking rate of the voice. |
| Read aloud automatically | on, off | Whether new lines are spoken without pressing *Listen*. |

A conversation keeps the language and the level it was started with. You can change both in Settings and still continue an older conversation as it was: it is judged in its own language at its own level. If its language differs from the one in Settings, it is also read with the voice it was started with.

Instead of saving a key in Settings you can set the environment variable `ANTHROPIC_API_KEY` or `OPENROUTER_API_KEY`. A saved key takes precedence.

## Where your data is

Nothing personal is kept in the program folder.

| What | Where |
|---|---|
| Settings | `%APPDATA%\Plauderbaum\settings.json` on Windows, `~/Library/Application Support/Plauderbaum/settings.json` on macOS |
| API keys | Windows Credential Manager, or the macOS login keychain, as *Plauderbaum* |
| Saved conversations, one file each | `%APPDATA%\Plauderbaum\conversations\` on Windows, `~/Library/Application Support/Plauderbaum/conversations/` on macOS |
| Browser profile of the app window | `%LOCALAPPDATA%\Plauderbaum\browser-profile\` on Windows, `~/Library/Caches/Plauderbaum/browser-profile/` on macOS |

The keys are not written to a file: they are kept in the credential store of your user account and can be viewed or removed there (Control Panel → Credential Manager). A key from an earlier version that still sits in `settings.json` is moved over at the next start. Instead of saving a key you can set the environment variable `ANTHROPIC_API_KEY` or `OPENROUTER_API_KEY`.

To remove everything the app has stored, delete those two `Plauderbaum` folders and the *Plauderbaum* entries in Credential Manager (Windows) or Keychain Access (macOS).

### What leaves your computer

- **To Anthropic or OpenRouter:** the scenario, the conversation so far and your new message, with every turn. With OpenRouter, the request is passed on to the provider of the model you chose. With a local model, nothing of this leaves your computer.
- **To Microsoft:** every line that is read aloud. The voices come from Microsoft's online text-to-speech service through the [`edge-tts`](https://github.com/rany2/edge-tts) library, which uses an unofficial interface and may stop working.
- **To OpenRouter:** a request for the public model list when you open the OpenRouter settings.

There is no telemetry and no account. The app's own server listens on `127.0.0.1` only and has no login, so anything running on the same computer can reach it while the app is open.

## Cost

**You pay for what the app uses.** Every model call is made with your API key and billed to your Anthropic or OpenRouter account at their prices. The author of this app has no part in that billing and takes no responsibility for what it costs you.

Each turn is one model call that carries the whole conversation so far. *Other reply* and starting a conversation are one call each. The voices are free. As a rough, unmeasured estimate, a long session with Claude Opus stays well under one US dollar, and Sonnet costs about half of that. Other models on OpenRouter can cost much more or much less.

The app does not count what it spends and has no limit of its own. To stay in control:

- Set a spending limit or use prepaid credit in your provider's console, and check your usage there.
- Create a key just for this app, so you can see what it uses and revoke it without affecting anything else.

## Your API key

**Keeping the key safe is your responsibility.** Whoever has it can spend your credit.

- The app stores the key in your user account's credential store and sends it only to the provider it belongs to. The page never gets to see a stored key.
- That does not protect it from other programs running under your user account. They can ask the credential store for the key, or use it through the app's local server while the app is open, which has no login.
- Do not use the app on a computer or user account you share with people you would not give the key to.
- If you think a key has leaked, revoke it in your provider's console and create a new one.

More detail, and how to report a security problem, is in [SECURITY.md](SECURITY.md).

## More documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): how it works inside, one turn step by step, the conversation tree, the code layout
- [CONTRIBUTING.md](CONTRIBUTING.md): running the tests, pull requests, releases
- [THIRD_PARTY.md](THIRD_PARTY.md): the packages and services the app uses, with their licences

## Other platforms

| | |
|---|---|
| Windows with Edge or Chrome | Works. This is what it is built and used on. |
| macOS with Edge, Chrome, Chromium, or Brave | Works. Start with `./run.sh`. Settings and conversations are kept in `~/Library/Application Support/Plauderbaum`, and the API keys in the login keychain. |
| Linux | Not supported yet. The Python code and the page are not tied to Windows, but there is no checked path for the app window. `./run.sh` still starts the server, and the page opens in the default browser. |
| Firefox | Untested. Firefox has no app-window mode, so the page would run as a normal tab at `http://127.0.0.1:8765` and the server would keep running until the console window is closed. |

## Known limits

- You type; there is no speech input and no feedback on pronunciation.
- The interface, the explanations and the translations are in English only.
- Saved conversations have no version number yet, so a later change of the format may make old ones unreadable.

## License

Plauderbaum is free software under the GNU General Public License, version 3 or (at your option) any later version. See [LICENSE](LICENSE). It comes without any warranty.

Happy learning!
