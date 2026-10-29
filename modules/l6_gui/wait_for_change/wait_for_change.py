from __future__ import annotations

import time

import numpy as np

from coproducer import call
from coproducer.result import Result, ok
from coproducer.services import get_service


def wait_for_change(timeout_s: float = 5.0, threshold: float = 0.002, poll_s: float = 0.2) -> Result:
    """Wait until FL Studio's window looks different from now (more than threshold of its pixels changed) or time runs out.

    Returns changed true or false and how long it waited. A timeout is not an error: the caller decides what it means.
    """
    ready = call("check_desktop_ready")
    if not ready.ok:
        return ready
    w, desk = ready.value, get_service("desktop")
    box = (w["left"], w["top"], w["left"] + w["width"], w["top"] + w["height"])
    base, start = desk.grab(box).astype(np.int16), time.monotonic()
    while time.monotonic() - start < timeout_s:
        time.sleep(poll_s)
        frac = float(np.mean(np.abs(desk.grab(box).astype(np.int16) - base).max(axis=2) > 8))
        if frac > threshold:
            return ok({"changed": True, "fraction": round(frac, 4), "waited_s": round(time.monotonic() - start, 2)})
    return ok({"changed": False, "fraction": 0.0, "waited_s": round(time.monotonic() - start, 2)})
