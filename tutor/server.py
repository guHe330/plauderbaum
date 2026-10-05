"""The local HTTP API behind the web page.

The server keeps no conversation state between requests: the page sends the
path of the conversation with every turn and stores the tree through
/api/conversations.
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi import Path as PathParam
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from . import roleplay
from .conversations import ConversationStore
from .errors import TutorError
from .keychain import KeyStore, KeyStoreError, SystemKeyStore
from .llm import openrouter
from .models import Conversation, ReplyRequest, StartRequest, TurnRequest
from .paths import APP_NAME, ASSETS, WEB
from .settings import LANGUAGES, MODELS, SettingsStore
from .speech import Speech

ConversationId = Annotated[str, PathParam(pattern=r"^[0-9a-f-]{36}$")]


class FreshStaticFiles(StaticFiles):
    """Static files the browser must revalidate, so an update shows up at once."""

    def file_response(self, *args, **kwargs) -> Response:
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response


def create_app(data: Path, keys: KeyStore | None = None) -> FastAPI:
    """The app, keeping settings and conversations in the folder `data`.

    The API keys go to `keys`, by default the system's credential store.
    """
    settings = SettingsStore(data / "settings.json", keys or SystemKeyStore())
    try:
        settings.move_plaintext_keys()
    except KeyStoreError:
        # Without a usable credential store the keys stay where they are and keep working.
        pass
    conversations = ConversationStore(data / "conversations")

    app = FastAPI(title=APP_NAME)
    app.mount("/web", FreshStaticFiles(directory=WEB), name="web")
    app.mount("/assets", StaticFiles(directory=ASSETS), name="assets")
    app.include_router(settings_routes(settings), prefix="/api")
    app.include_router(speech_routes(settings, Speech()), prefix="/api")
    app.include_router(roleplay_routes(settings), prefix="/api")
    app.include_router(conversation_routes(conversations), prefix="/api")

    @app.get("/")
    def index():
        return FileResponse(WEB / "index.html", headers={"Cache-Control": "no-cache"})

    @app.exception_handler(TutorError)
    def tutor_error(_request, error: TutorError):
        return JSONResponse(status_code=502, content={"detail": str(error)})

    return app


def settings_routes(settings: SettingsStore) -> APIRouter:
    router = APIRouter()

    @router.get("/settings")
    def get_settings():
        return {"settings": settings.load().public(), "languages": LANGUAGES, "models": MODELS}

    @router.post("/settings")
    def post_settings(changes: dict):
        try:
            return {"settings": settings.save(changes).public()}
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error))
        except KeyStoreError as error:
            raise HTTPException(status_code=500, detail=str(error))

    @router.get("/openrouter-models")
    def get_openrouter_models():
        try:
            return openrouter.structured_output_models()
        except (OSError, ValueError, KeyError):
            raise HTTPException(status_code=502, detail="Could not load the OpenRouter model list.")

    return router


def speech_routes(settings: SettingsStore, speech: Speech) -> APIRouter:
    router = APIRouter()

    @router.get("/voices")
    async def get_voices(lang: str):
        try:
            return await speech.voices(lang)
        except Exception:
            raise HTTPException(status_code=502, detail="Could not load the voice list. Check your internet connection.")

    @router.get("/tts")
    async def tts(text: str):
        text = text.strip()[:1000]
        if not text:
            raise HTTPException(status_code=400, detail="Nothing to say.")
        current = settings.load()
        try:
            audio = await speech.synthesize(text, current.voice, current.speech_rate)
        except Exception:
            raise HTTPException(status_code=502, detail="The voice service did not answer.")
        return Response(content=audio, media_type="audio/mpeg")

    return router


def roleplay_routes(settings: SettingsStore) -> APIRouter:
    router = APIRouter()

    @router.get("/scenarios")
    def get_scenarios():
        return roleplay.SCENARIOS

    @router.post("/start")
    def start(request: StartRequest):
        return roleplay.open_conversation(settings.load(), request.scenario)

    @router.post("/turn")
    def turn(request: TurnRequest):
        return roleplay.judge_turn(
            settings.load(), request.scenario, request.situation, request.path, request.text,
        )

    @router.post("/reply")
    def reply(request: ReplyRequest):
        if request.path and request.path[-1].role != "learner":
            raise HTTPException(status_code=400, detail="There is no learner line to reply to.")
        return roleplay.other_reply(
            settings.load(), request.scenario, request.situation, request.path, request.existing,
        )

    return router


def conversation_routes(conversations: ConversationStore) -> APIRouter:
    router = APIRouter()

    @router.get("/conversations")
    def list_conversations():
        return conversations.list_all()

    @router.get("/conversations/{conversation_id}")
    def get_conversation(conversation_id: ConversationId):
        conversation = conversations.load(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="This conversation no longer exists.")
        return conversation

    @router.put("/conversations/{conversation_id}")
    def put_conversation(conversation_id: ConversationId, conversation: Conversation):
        try:
            saved = conversations.save(conversation_id, conversation.model_dump())
        except OSError:
            raise HTTPException(status_code=500, detail="Could not save the conversation.")
        return {"updated": saved["updated"]}

    @router.delete("/conversations/{conversation_id}")
    def delete_conversation(conversation_id: ConversationId):
        conversations.delete(conversation_id)
        return {}

    return router
