"""Wake word detection (MASTER_SPEC M3) — openWakeWord, on-device, free.

Feed 16 kHz int16 mic frames in ~80 ms chunks via feed(); when the
configured model's score crosses the threshold, you get True (and a
refractory window starts so one wake phrase can't fire twice).

Model comes from ARIA_WAKE_MODEL: a built-in pretrained name
("hey_jarvis" ships with openwakeword) or a path to a custom
"hey aria" model trained at openwakeword.com/train.
"""

from pathlib import Path

import numpy as np

from backend.core.config import get_settings

CHUNK_MS = 80
CHUNK_SAMPLES = 16_000 * CHUNK_MS // 1000  # 1280
REFRACTORY_CHUNKS = 25  # ~2s of silence after a hit before it can re-fire


class WakeDetector:
    def __init__(self) -> None:
        from openwakeword.model import Model  # heavy import; keep lazy

        settings = get_settings()
        self.threshold = settings.wake_threshold
        self._cooldown = 0
        requested = settings.wake_model
        if Path(requested).suffix in (".onnx", ".tflite"):
            model_paths = [requested]
        else:
            from openwakeword import get_pretrained_model_paths

            all_paths = get_pretrained_model_paths(inference_framework="onnx")
            model_paths = [p for p in all_paths if requested in str(p)]
            if not model_paths:
                raise SystemExit(
                    f"unknown wake model '{requested}' — pretrained options: "
                    "alexa, hey_mycroft, hey_jarvis, hey_rhasspy, timer, weather"
                )
        self._model = Model(wakeword_models=model_paths, inference_framework="onnx")
        self.name = requested
        self.hit = False

    def feed(self, chunk: np.ndarray, return_scores: bool = False) -> bool | dict[str, float]:
        """Consume one int16 chunk (≈CHUNK_SAMPLES samples). Returns True on wake."""
        flat = chunk.flatten()
        scores: dict[str, float] = self._model.predict(flat)
        self.hit = False
        if self._cooldown > 0:
            self._cooldown -= 1
        elif any(s >= self.threshold for s in scores.values()):
            self._cooldown = REFRACTORY_CHUNKS
            self.hit = True
        return scores if return_scores else self.hit


def ensure_models_downloaded() -> None:
    """Fetch pretrained models on first run (needs internet once)."""
    from openwakeword.utils import download_models

    download_models()
