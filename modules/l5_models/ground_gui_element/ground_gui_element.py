from __future__ import annotations

from pathlib import Path

from coproducer import call
from coproducer.result import Result, fail


def ground_gui_element(image_path: str, description: str, min_confidence: float = 0.0) -> Result:
    """Find a described interface element on a screenshot and return its screen coordinates {x, y, confidence}.

    Errors: E_MODEL when no grounding model is configured (recipes then use hotkeys and fixed anchors), E_GUI_MISMATCH
    when the confidence is under min_confidence.
    """
    if not Path(image_path).is_file():
        return fail("E_NOT_FOUND", "no screenshot at %s" % Path(image_path).name)
    got = call("run_model_op", model="vision", op="ground", args={"image_path": image_path, "description": description}, timeout_s=120)
    if got.ok and got.value["confidence"] < min_confidence:
        return fail("E_GUI_MISMATCH", "confidence %.2f is under %.2f" % (got.value["confidence"], min_confidence), found=got.value)
    return got
