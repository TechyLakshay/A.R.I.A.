"""Audio I/O for the voice loop (MASTER_SPEC M2).

One module owns all device handling: mic capture at 16 kHz PCM16 mono
(Porcupine + Realtime input format) and playback at 24 kHz (Realtime
output format).
"""

import numpy as np
import sounddevice as sd

IN_RATE = 16_000
OUT_RATE = 24_000
CHANNELS = 1
DTYPE = "int16"


def list_devices() -> str:
    return str(sd.query_devices())


def record_seconds(seconds: float, device: int | None = None) -> np.ndarray:
    """Record from the default (or given) mic. Returns int16 samples, shape (n, 1)."""
    chunks: list[np.ndarray] = []

    def callback(indata: np.ndarray, frames: int, time_info: object, status: object) -> None:
        chunks.append(indata.copy())

    with sd.InputStream(
        samplerate=IN_RATE, channels=CHANNELS, dtype=DTYPE,
        device=device, callback=callback,
    ):
        sd.sleep(int(seconds * 1000))

    if not chunks:
        return np.empty((0, CHANNELS), dtype=np.int16)
    return np.concatenate(chunks)


def play_pcm16(samples: np.ndarray, rate: int = OUT_RATE, device: int | None = None) -> None:
    """Blocking playback of int16 samples."""
    sd.play(samples, samplerate=rate, device=device)
    sd.wait()


def peak_rms(samples: np.ndarray) -> tuple[int, float]:
    """(peak, rms) over int16 samples — quick 'did the mic actually hear anything' check."""
    f = samples.astype(np.float64)
    return int(np.abs(f).max()), float(np.sqrt((f**2).mean()))
