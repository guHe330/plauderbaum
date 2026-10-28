# Third-party software and services

Plauderbaum is built on the work of others. None of it is included in this repository or in the release zip: `run.bat` downloads the Python packages from [PyPI](https://pypi.org/) at the first start, in exactly the versions pinned in `requirements.txt`.

## Python packages the app imports

| Package | Used for | Licence |
|---|---|---|
| [anthropic](https://github.com/anthropics/anthropic-sdk-python) | Client for the Claude API | MIT |
| [edge-tts](https://github.com/rany2/edge-tts) | The voices: Microsoft's online text-to-speech | LGPL-3.0 |
| [fastapi](https://github.com/fastapi/fastapi) | The local HTTP API behind the page | MIT |
| [keyring](https://github.com/jaraco/keyring) | Stores the API keys in the system's credential store | MIT |
| [uvicorn](https://uvicorn.dev/) | The web server that runs the FastAPI app | BSD-3-Clause |

Everything else on the Python side is the standard library, including the calls to OpenRouter.

<details>
<summary>The 33 packages those five bring along</summary>

- **MIT:** annotated-doc, annotated-types, anyio, attrs, docstring-parser, h11, jaraco-classes, jaraco-context, jaraco-functools, jiter, more-itertools, pydantic, pydantic-core, tabulate, truststore, typing-inspection
- **Apache-2.0:** aiosignal, frozenlist, multidict, opentelemetry-api, propcache, yarl
- **BSD-3-Clause:** click, httpcore2, httpx2, idna, pywin32-ctypes, starlette
- **PSF-2.0:** aiohappyeyeballs, typing-extensions
- **Apache-2.0 AND MIT:** aiohttp
- **MPL-2.0:** certifi
- **MIT OR Apache-2.0:** sniffio

</details>

Licences are as declared in each package's own metadata at the pinned version.

## The page

No third-party JavaScript, CSS or fonts. It is plain HTML, CSS and JavaScript modules, and uses the fonts of your system.

## Services the app talks to

Each has terms of its own, which apply to you as the one using your key or connection:

- [Anthropic API](https://www.anthropic.com/legal/commercial-terms) or [OpenRouter](https://openrouter.ai/terms) for the model
- Microsoft's online text-to-speech service for the voices, reached through `edge-tts` over an unofficial interface

## Only for development

- [pip-tools](https://github.com/jazzband/pip-tools) (BSD-3-Clause) generates `requirements.txt`
- Node.js runs the JavaScript tests with its built-in test runner
- GitHub Actions: `actions/checkout`, `actions/setup-python`, `actions/setup-node` and `actions/attest-build-provenance`

## Artwork

The icon and the banner were made with Claude for this project and are covered by the project's licence.

