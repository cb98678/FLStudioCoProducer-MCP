from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok


def set_tempo_and_swing(bpm: float, swing: float) -> Result:
    """Set the tempo and the global channel swing (0.0 to 1.0) together, confirming both by readback.

    Errors come from the two verified setters: E_ARG, E_NOT_VERIFIED.
    """
    t = call("set_tempo_verified", bpm=bpm)
    if not t.ok:
        return t
    s = call("set_swing_verified", swing=swing)
    if not s.ok:
        return s
    return ok({"bpm": t.value, "swing": s.value}, verified=True)
