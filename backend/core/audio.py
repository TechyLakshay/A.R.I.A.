"""Audio I/O for the voice loop (MASTER_SPEC M2/M4).

One module owns all device handling: mic capture at 16 kHz PCM16 mono
(wake word + Realtime input format) and playback at 24 kHz (Realtime
output format).
"""

import queue

import numpy as np
import sounddevice as sd

IN_RATE = 16_000
OUT_RATE = 24_000
CHANNELS = 1
DTYPE = "int16"


def list_devices() -> str:
    return str(sd.query_devices())


class AudioPlayer:
    """Continuous 24 kHz PCM16 playback. write() is safe from any thread.

    When voice FX are enabled, every chunk runs through a small DSP chain
    (high-pass → presence EQ → compressor → short reverb → trim) before
    hitting the speakers — the 'voice in a helmet' texture.
    """

    def __init__(self, rate: int = OUT_RATE, effects: bool = True) -> None:
        self._rate = rate
        self._q: queue.Queue[bytes] = queue.Queue()
        self._buf = b""
        self._board = _voice_board() if effects else None
        if effects and self._board is None:
            print("voice FX requested but pedalboard unavailable — playing dry", flush=True)
        self._stream = sd.OutputStream(
            samplerate=rate, channels=1, dtype="int16", callback=self._fill
        )
        self._stream.start()

    def _fill(self, outdata: np.ndarray, frames: int, time_info: object, status: object) -> None:
        need = frames * 2  # bytes (int16 mono)
        while len(self._buf) < need:
            try:
                self._buf += self._q.get_nowait()
            except queue.Empty:
                break
        have = min(need, len(self._buf))
        have -= have % 2  # whole int16 samples only
        if have == 0:
            outdata[:] = 0
            return
        arr = np.frombuffer(self._buf[:have], dtype=np.int16)
        self._buf = self._buf[have:]
        outdata[: len(arr), 0] = arr
        outdata[len(arr):, 0] = 0

    def write(self, pcm16_bytes: bytes) -> None:
        if self._board is not None:
            try:
                pcm16_bytes = _apply_board(self._board, pcm16_bytes, self._rate)
            except Exception:
                pass  # a bad FX chunk must never kill playback
        self._q.put(pcm16_bytes)

    def drain(self) -> None:
        """Drop anything queued (e.g. on session close)."""
        while not self._q.empty():
            self._q.get_nowait()
        self._buf = b""

    def close(self) -> None:
        self._stream.stop()
        self._stream.close()


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


def _voice_board():
    """The JARVIS texture: cut rumble, add presence, tame peaks, small room tail.

    Returns None if pedalboard is unavailable (V1 keeps playing dry).
    """
    try:
        from pedalboard import (
            Compressor,
            Gain,
            HighpassFilter,
            PeakFilter,
            Pedalboard,
            Reverb,
        )

        return Pedalboard([
            HighpassFilter(cutoff_frequency_hz=140),
            PeakFilter(cutoff_frequency_hz=3200, gain_db=3.0, q=0.8),
            Compressor(threshold_db=-18, ratio=2.5, attack_ms=5, release_ms=80),
            Reverb(room_size=0.28, damping=0.55, wet_level=0.12, dry_level=0.9, width=0.6),
            Gain(gain_db=-1.5),
        ])
    except Exception:
        return None


def _apply_board(board, pcm16: bytes, rate: int) -> bytes:
    arr = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32) / 32768.0
    out = board(arr, rate)
    return (np.clip(out, -1.0, 1.0) * 32767.0).astype(np.int16).tobytes()
