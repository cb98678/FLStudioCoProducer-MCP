from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail
from coproducer.services import get_service


def locate_element(description: str, min_confidence: float = 0.5) -> Result:
    """Take a screenshot of FL Studio and ask the vision model where a described element is. Returns window pixels {x, y, confidence}.

    Errors: E_MODEL without a grounding model, E_GUI_MISMATCH below min_confidence. Never clicks.
    """
    root = get_service("sandbox_root")
    if root is None:
        return fail("E_SANDBOX_VIOLATION", "no sandbox folder")
    shot = call("take_screenshot", out_path=str(root) + "/screens/_locate.png")
    if not shot.ok:
        return shot
    return call("ground_gui_element", image_path=shot.value["path"], description=description, min_confidence=min_confidence)
