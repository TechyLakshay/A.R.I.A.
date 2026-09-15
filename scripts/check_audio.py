"""M2 acceptance check: list devices, or record 5s and play it back.

Usage (from repo root):
    python scripts/check_audio.py devices   # show input/output devices
    python scripts/check_audio.py test      # record 5s, print levels, play back
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import sounddevice as sd  # noqa: E402

from backend.core.audio import IN_RATE, list_devices, peak_rms, play_pcm16, record_seconds  # noqa: E402


def show_devices() -> None:
    print(list_devices())


def record_and_playback() -> None:
    print(f"Recording 5s at {IN_RATE} Hz — SPEAK NOW…")
    samples = record_seconds(5.0)
    peak, rms = peak_rms(samples)
    print(f"captured {samples.shape[0]} samples ({samples.shape[0] / IN_RATE:.2f}s)")
    print(f"peak={peak} rms={rms:.0f}")
    if peak < 200:
        print("WARNING: mic picked up near-silence — check the input device/permissions")
    print("Playing back…")
    play_pcm16(samples, rate=IN_RATE)
    print("Done. If you heard yourself clearly, M2 acceptance passes.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    if mode == "devices":
        show_devices()
    else:
        record_and_playback()
