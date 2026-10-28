# How Plauderbaum works

```
 app window (Edge/Chrome, --app mode)
 └─ web/  plain HTML, CSS, JavaScript modules, no build step
      │  HTTP, 127.0.0.1:8765
 tutor/ Python package: FastAPI app served by uvicorn
      ├─ roleplay ──► llm ──► Anthropic API  or  OpenRouter
      ├─ speech   ──► Microsoft neural voices (edge-tts)
      ├─ settings ──► %APPDATA%\Plauderbaum\settings.json
      └─ conversations ► %APPDATA%\Plauderbaum\conversations\*.json
```

It is not Electron. `run.bat` starts a Python web server on your own machine and opens its page in an Edge or Chrome window without browser controls. The window uses a profile of its own, so it is a separate process, and the server stops when that process ends.

## One turn

1. The page sends the scenario, the path of the conversation that is currently shown, and your new message to `POST /api/turn`.
2. `roleplay` builds the prompt. `llm` sends it to the chosen provider and requires a JSON object with a fixed shape: a verdict (`ok`, `has_errors`, `other_language`, `question`, `unclear`), the ideal sentence, alternatives, an explanation, and the other person's next line.
3. The answer is checked against that shape. Anything else is reported as an unreadable answer and never reaches the page.
4. The model only delivers the verdict; the app decides what happens next. On `ok`, the page adds your line and the reply to the tree. On anything else it shows the correction and stays where it was.

The model only ever sees your lines in their corrected form, so earlier mistakes do not pile up in the conversation.

## The conversation tree

A conversation is a tree of lines in which tutor and learner alternate. Rewinding and answering again, or asking for another reply, adds a sibling to an existing line instead of replacing it. The conversation on screen is one path through the tree, from the opening line to the line it currently ends on. Each line remembers which of its answers was shown last, so switching back to a branch continues where you left it. An answer that matches an earlier one at the same point, ignoring case and punctuation, returns to that branch instead of adding a sibling.

The server keeps no conversation state between requests. The page owns the tree, sends the relevant path with every model call, and stores the whole tree through `PUT /api/conversations/{id}` after every change. Failed attempts and correction cards are not part of the tree; a learner line only records how many attempts failed before it was accepted.

## Code layout

```
run.bat               starter on Windows: creates .venv on first run, then `python -m tutor`
run.sh                the same starter for macOS
requirements.in       the packages used directly
requirements.txt      generated from it: every package pinned, with hashes
tutor/
  __main__.py         starts the server and the app window, stops with the window
  server.py           HTTP routes; builds the app from a data folder
  roleplay.py         scenarios, prompts, answer formats; the three model tasks
  llm/                one prompt in, one checked JSON object out
    claude.py           Anthropic API
    openrouter.py       OpenRouter API and its model list
    answer.py           parses and checks the model's answer
  models.py           the data exchanged with the page and saved to disk
  settings.py         the settings, their allowed values, their file
  keychain.py         the API keys in the system's credential store
  conversations.py    saved conversations, one JSON file each
  speech.py           text-to-speech with a small cache
  window.py           finds Edge or Chrome and opens the app window
  paths.py            program folder and per-user data folders
  errors.py           the error type whose message is shown to the learner
web/
  index.html, style.css
  main.js             entry point
  tree.js             the conversation tree; knows nothing of page or server
  session.js          what happens in an open conversation
  chat-view.js        draws a conversation; reports clicks to session.js
  tree-view.js        draws the whole tree in the sidebar
  home.js             start page: scenarios, own topic, earlier conversations
  settings.js         the Settings tab
  store.js            loading and saving conversations on the server
  speech.js           playback queue for spoken lines
  navigation.js       tabs and pages
  api.js, dom.js, state.js   small shared helpers
tests/                unit tests for both sides
.github/              CI, the release and dependency-update workflows, issue forms
docs/                 the banner, the README screenshots and this file
tools/                the shortcut script
packaging/            builds the download package for a release
```

Dependencies are deliberately few: `fastapi` with `uvicorn` to serve it, `anthropic` for the Claude API, `edge-tts` for the voices, and `keyring` for the credential store. OpenRouter is called with Python's standard library. The page uses no framework and no packages.

