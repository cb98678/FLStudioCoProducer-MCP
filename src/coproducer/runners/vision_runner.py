"""GUI grounding: screenshot plus a description gives screen coordinates.

No model is chosen yet: `coproducer bench-vision` decides (candidates in the plan: UGround, GUI-Actor and others).
Until then this runner answers E_MODEL, and the GUI recipes use hotkeys and recorded anchors only.
Plug a model in by setting COPRODUCER_VISION_ADAPTER to a module with ground(image_path, description) -> (x, y, confidence).
"""
from __future__ import annotations

import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner_common import RunnerError, serve  # noqa: E402


def ground(a: dict) -> dict:
    name = os.environ.get("COPRODUCER_VISION_ADAPTER", "")
    if not name:
        raise RunnerError("E_MODEL", "no GUI grounding model is configured; run bench-vision and set COPRODUCER_VISION_ADAPTER")
    x, y, conf = importlib.import_module(name).ground(a["image_path"], a["description"])
    return {"x": int(x), "y": int(y), "confidence": float(conf)}


if __name__ == "__main__":
    serve({"load": lambda a: {"loaded": a.get("variant")}, "unload": lambda a: True, "ping": lambda a: "pong", "ground": ground})
