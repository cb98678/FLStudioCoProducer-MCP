from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok
from coproducer.services import get_service


def drag_between(x1: int, y1: int, x2: int, y2: int, seconds: float = 0.4) -> Result:
    """Drag with the left button from one point to another, both in FL Studio window pixels."""
    ready = call("check_desktop_ready")
    if not ready.ok:
        return ready
    w = ready.value
    if any(not (0 <= x < w["width"] and 0 <= y < w["height"]) for x, y in ((x1, y1), (x2, y2))):
        return fail("E_ARG", "both points must be inside the %dx%d window" % (w["width"], w["height"]))
    get_service("desktop").drag(w["left"] + x1, w["top"] + y1, w["left"] + x2, w["top"] + y2, seconds)
    return ok({"from": [x1, y1], "to": [x2, y2]})
