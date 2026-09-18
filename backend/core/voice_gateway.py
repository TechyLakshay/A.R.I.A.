"""Voice gateway: the state machine at the heart of A.R.I.A. (MASTER_SPEC §2, §7a).

idle → (wake) → listening → (server VAD end of turn) → speaking → listening
→ (ARIA_FOLLOWUP_WINDOW_S of silence) → idle.

Thread world: one mic stream feeds the wake detector and the session.
Async world: RealtimeSession events drive state changes and playback.
Mic is muted while speaking (no echo loop — MASTER_SPEC risk #4).
"""

import asyncio
import base64
import queue
import threading
import time

import numpy as np
import sounddevice as sd

from backend.core.audio import IN_RATE, AudioPlayer
from backend.core.events import broadcast
from backend.core.realtime import RealtimeSession
from backend.core.wake import CHUNK_SAMPLES, WakeDetector

STATES = ("idle", "listening", "speaking")


class VoiceGateway:
    def __init__(self) -> None:
        self.state = "idle"
        self.session: RealtimeSession | None = None
        self.player: AudioPlayer | None = None
        self.last_activity = 0.0
        self._loop: asyncio.AbstractEventLoop | None = None
        self._text = ""

    # ---------- lifecycle ----------
    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        from backend.core.config import get_settings

        self._loop = loop
        self.player = AudioPlayer(effects=get_settings().voice_fx)
        threading.Thread(target=self._mic_loop, name="voice-gateway", daemon=True).start()

    # ---------- thread world (mic) ----------
    def _mic_loop(self) -> None:
        from backend.core.config import get_settings

        debug = get_settings().log_level.upper() == "DEBUG"
        detector = WakeDetector()
        print("gateway mic stream opening…", flush=True)
        audio_q: queue.Queue[np.ndarray] = queue.Queue()

        def callback(indata: np.ndarray, frames: int, time_info: object, status: object) -> None:
            audio_q.put(indata.copy())

        buffer = np.empty((0, 1), dtype=np.int16)
        window_max = 0.0
        window_rms = 0.0
        window_n = 0
        window_start = time.time()
        with sd.InputStream(samplerate=IN_RATE, channels=1, dtype="int16", callback=callback):
            print("gateway mic stream open — listening for wake phrase", flush=True)
            while True:
                buffer = np.concatenate([buffer, audio_q.get()])
                while buffer.shape[0] >= CHUNK_SAMPLES:
                    chunk, buffer = buffer[:CHUNK_SAMPLES], buffer[CHUNK_SAMPLES:]
                    if self.state == "idle":
                        scores = detector.feed(chunk, return_scores=True)
                        window_max = max(window_max, max(scores.values(), default=0.0))
                        window_rms += float(np.abs(chunk.astype(np.float64)).mean())
                        window_n += 1
                        if debug and time.time() - window_start >= 2.0:
                            print(
                                f"[gateway] wake score max {window_max:.3f} · mic rms {window_rms / max(window_n, 1):.0f}",
                                flush=True,
                            )
                            window_start, window_max, window_rms, window_n = time.time(), 0.0, 0.0, 0
                        if detector.hit:
                            print("wake detected — opening session", flush=True)
                            asyncio.run_coroutine_threadsafe(self._open_session(), self._loop)
                    elif self.state == "listening":
                        if time.time() - self.last_activity > _followup_window():
                            asyncio.run_coroutine_threadsafe(
                                self._close_session("follow-up window elapsed"), self._loop
                            )
                        elif self.session is not None:
                            self.session.send_audio_threadsafe(chunk.tobytes(), self._loop)
                    # speaking: mic muted — drop frames

    # ---------- async world (session + events) ----------
    async def _open_session(self) -> None:
        try:
            self.session = RealtimeSession(on_event=self._on_realtime_event)
            await self.session.start()
            self._set_state("listening")
        except Exception as exc:  # bad key, no network, …
            print(f"session open failed: {exc}", flush=True)
            await broadcast({"type": "error", "message": f"voice service unavailable: {exc}"})
            self._set_state("idle")

    async def _close_session(self, reason: str) -> None:
        if self.session is not None:
            await self.session.close()
            self.session = None
        if self.player is not None:
            self.player.drain()
        self._text = ""
        self._set_state("idle")
        print(f"session closed ({reason})", flush=True)

    async def _on_realtime_event(self, ev: dict) -> None:
        etype = ev.get("type", "")
        if etype == "input_audio_buffer.speech_started":
            self.last_activity = time.time()
        elif etype == "input_audio_buffer.speech_stopped":
            self.last_activity = time.time()
        elif etype == "conversation.item.input_audio_transcription.completed":
            text = ev.get("transcript", "")
            if text:
                await broadcast({"type": "transcript.final", "text": text})
        elif etype == "response.created":
            self._text = ""
            self._set_state("speaking")
        elif etype in ("response.output_audio.delta", "response.audio.delta"):
            if self.player is not None:
                self.player.write(base64.b64decode(ev.get("delta", "")))
        elif etype in ("response.output_audio_transcript.delta", "response.audio_transcript.delta"):
            self._text += ev.get("delta", "")
        elif etype in ("response.output_audio_transcript.done", "response.audio_transcript.done"):
            await broadcast({"type": "assistant.transcript", "text": ev.get("transcript", self._text)})
        elif etype == "response.done":
            self.last_activity = time.time()
            self._set_state("listening")
        elif etype == "error":
            print(f"realtime error: {ev.get('error')}", flush=True)
            await broadcast({"type": "error", "message": str(ev.get("error", {}).get("message", "voice error"))})
        elif etype == "aria.session_closed":
            await self._close_session(etype)

    # ---------- shared ----------
    def _set_state(self, state: str) -> None:
        if state == self.state:
            return
        self.state = state
        if state == "listening":
            self.last_activity = time.time()
        if self._loop is not None:
            asyncio.run_coroutine_threadsafe(broadcast({"type": "state", "state": state}), self._loop)


def _followup_window() -> float:
    from backend.core.config import get_settings

    return get_settings().followup_window_s


_gateway: VoiceGateway | None = None


def start(loop: asyncio.AbstractEventLoop) -> None:
    global _gateway
    _gateway = VoiceGateway()
    _gateway.start(loop)


def get() -> VoiceGateway | None:
    return _gateway
