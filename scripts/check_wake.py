"""M3 acceptance check: live wake-word detection from the mic.

Usage (from repo root):
    python scripts/check_wake.py            # listen; print WAKE on trigger (Ctrl+C to stop)
    python scripts/check_wake.py models     # show loaded model + score stream
"""

import queue
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import sounddevice as sd  # noqa: E402

from backend.core.audio import IN_RATE  # noqa: E402
from backend.core.wake import CHUNK_SAMPLES, WakeDetector, ensure_models_downloaded  # noqa: E402


def main() -> None:
    seconds = float(sys.argv[-1]) if sys.argv[-1].replace(".", "").isdigit() else None
    ensure_models_downloaded()
    detector = WakeDetector()
    print(f"wake model: {detector.name} · threshold {detector.threshold}", flush=True)
    print("Say the wake phrase out loud…", flush=True)

    audio_q: queue.Queue[np.ndarray] = queue.Queue()

    def callback(indata: np.ndarray, frames: int, time_info: object, status: object) -> None:
        audio_q.put(indata.copy())

    buffer = np.empty((0, 1), dtype=np.int16)
    woke = 0
    started = time.time()
    window_start = started
    window_max = 0.0
    with sd.InputStream(samplerate=IN_RATE, channels=1, dtype="int16", callback=callback):
        while True:
            if seconds and time.time() - started > seconds:
                break
            buffer = np.concatenate([buffer, audio_q.get(timeout=5)])
            while buffer.shape[0] >= CHUNK_SAMPLES:
                chunk, buffer = buffer[:CHUNK_SAMPLES], buffer[CHUNK_SAMPLES:]
                scores = detector.feed(chunk, return_scores=True)
                window_max = max(window_max, max(scores.values(), default=0.0))
                if time.time() - window_start >= 0.5:
                    print(f"max score last 0.5s: {window_max:.3f}", flush=True)
                    window_start, window_max = time.time(), 0.0
                if detector.hit:
                    woke += 1
                    print(f"WAKE #{woke} — phrase detected!", flush=True)
    print(f"done: {woke} wake(s) in {seconds or '∞'}s", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nstopped")
