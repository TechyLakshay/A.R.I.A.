"""Background mic loop feeding the wake detector; broadcasts wake events."""

import asyncio
import queue
import threading

import numpy as np
import sounddevice as sd

from backend.core.audio import IN_RATE
from backend.core.events import broadcast
from backend.core.wake import CHUNK_SAMPLES, WakeDetector


def start(loop: asyncio.AbstractEventLoop) -> None:
    detector = WakeDetector()
    print(f"wake loop started (model: {detector.name})", flush=True)
    audio_q: queue.Queue[np.ndarray] = queue.Queue()

    def callback(indata: np.ndarray, frames: int, time_info: object, status: object) -> None:
        audio_q.put(indata.copy())

    def run() -> None:
        buffer = np.empty((0, 1), dtype=np.int16)
        with sd.InputStream(samplerate=IN_RATE, channels=1, dtype="int16", callback=callback):
            while True:
                buffer = np.concatenate([buffer, audio_q.get()])
                while buffer.shape[0] >= CHUNK_SAMPLES:
                    chunk, buffer = buffer[:CHUNK_SAMPLES], buffer[CHUNK_SAMPLES:]
                    if detector.feed(chunk):
                        asyncio.run_coroutine_threadsafe(
                            broadcast({"type": "wake", "model": detector.name}), loop
                        )

    threading.Thread(target=run, name="wake-loop", daemon=True).start()
