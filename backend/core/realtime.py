"""One conversation with the OpenAI Realtime API (MASTER_SPEC M4).

Async world: lives on the event loop. The mic thread pushes audio in
via send_audio_threadsafe(); model audio/text comes back through
on_event callbacks. Server VAD owns turn detection; we never parse
audio timing here.
"""

import asyncio
import base64
import json
from typing import Awaitable, Callable

import websockets

from backend.core.config import get_settings

PERSONA = (
    "You are A.R.I.A., a warm, concise voice assistant. "
    "Answer in 1-3 spoken sentences unless asked for detail. "
    "Never use markdown, emoji, or lists — everything you say is spoken aloud. "
    "Always respond in English only, regardless of the user's accent; "
    "never translate, never switch to any other language."
)


class RealtimeSession:
    def __init__(self, on_event: Callable[[dict], Awaitable[None]]) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set (.env)")
        self._on_event = on_event
        self._ws: websockets.WebSocketClientProtocol | object | None = None
        self._model = settings.realtime_model

    async def start(self) -> None:
        url = f"wss://api.openai.com/v1/realtime?model={self._model}"
        headers = {"Authorization": f"Bearer {get_settings().openai_api_key}"}
        try:
            self._ws = await websockets.connect(url, additional_headers=headers, max_size=None)
        except TypeError:  # websockets < 14 uses extra_headers
            self._ws = await websockets.connect(url, extra_headers=headers, max_size=None)
        asyncio.create_task(self._recv_loop())
        await self._send({
            "type": "session.update",
            "session": {
                "type": "realtime",
                "instructions": PERSONA,
                "audio": {
                    "input": {
                        "format": "pcm16",
                        "transcription": {"model": "gpt-4o-mini-transcribe", "language": "en"},
                        "turn_detection": {"type": "server_vad"},
                    },
                    "output": {"format": "pcm16", "voice": get_settings().voice},
                },
            },
        })

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()
            self._ws = None

    # --- mic thread side -------------------------------------------------
    def send_audio_threadsafe(self, pcm16: bytes, loop: asyncio.AbstractEventLoop) -> None:
        if self._ws is None:
            return
        asyncio.run_coroutine_threadsafe(self._send_audio(pcm16), loop)

    async def _send_audio(self, pcm16: bytes) -> None:
        await self._send({
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(pcm16).decode("ascii"),
        })

    # --- internals --------------------------------------------------------
    async def _send(self, payload: dict) -> None:
        if self._ws is not None:
            await self._ws.send(json.dumps(payload))

    async def _recv_loop(self) -> None:
        try:
            async for raw in self._ws:
                await self._on_event(json.loads(raw))
        except websockets.ConnectionClosed:
            await self._on_event({"type": "aria.session_closed", "reason": "connection closed"})
