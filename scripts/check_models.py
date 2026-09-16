"""One-time: download openWakeWord pretrained models and list them."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openwakeword.utils import download_models  # noqa: E402

download_models()
print("models downloaded OK")
