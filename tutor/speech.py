"""Text-to-speech with Microsoft's online neural voices, through edge-tts."""

import edge_tts


class Speech:
    """Lists voices and turns lines into MP3 audio, remembering recent ones."""

    def __init__(self, cache_size: int = 200):
        self._cache_size = cache_size
        self._cache: dict[tuple[str, str, str], bytes] = {}
        self._voices: list[dict] | None = None

    async def voices(self, language: str) -> list[dict]:
        """The voices for a two-letter language code, as {id, label}."""
        if self._voices is None:
            self._voices = await edge_tts.list_voices()
        return [
            {"id": v["ShortName"], "label": _label(v)}
            for v in self._voices
            if v["Locale"].split("-")[0] == language
        ]

    async def synthesize(self, text: str, voice: str, rate: str) -> bytes:
        """MP3 audio for `text`."""
        key = (text, voice, rate)
        audio = self._cache.get(key)
        if audio is None:
            chunks = []
            async for chunk in edge_tts.Communicate(text, voice, rate=rate).stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            audio = b"".join(chunks)
            if len(self._cache) >= self._cache_size:
                self._cache.pop(next(iter(self._cache)))  # the oldest entry
            self._cache[key] = audio
        return audio


def _label(voice: dict) -> str:
    name = voice["ShortName"].split("-")[-1].removesuffix("Neural")
    return f"{name} ({voice['Locale']}, {voice['Gender']})"
