from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def click_at(x: int, y: int, button: str = "left", clicks: int = 1) -> Result:
    """Click at a point given in FL Studio window pixels (the same coordinates as a take_screenshot image).

    Errors: E_ARG when the point is outside the window, plus every refusal of check_desktop_ready.
    """
    ready = call("check_desktop_ready")
    if not ready.ok:
        return ready
    w = ready.value
    if not (0 <= x < w["width"] and 0 <= y < w["height"]):
        return fail("E_ARG", "point (%d, %d) is outside the %dx%d window" % (x, y, w["width"], w["height"]))
    get_service("desktop").click(w["left"] + x, w["top"] + y, button, clicks)
    return ok({"clicked": [x, y], "screen": [w["left"] + x, w["top"] + y]})
