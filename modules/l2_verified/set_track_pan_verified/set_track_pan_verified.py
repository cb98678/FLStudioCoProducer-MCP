from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_track_pan_verified(index: int, pan: float) -> Result:
    """Set a mixer track's pan from -1.0 (left) to 1.0 (right) and confirm by reading it back.

    Errors: E_ARG for bad input or an FL-side failure, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_mixer_set_track_pan", index=index, pan=pan)
    if not w.ok:
        return w
    r = call("op_mixer_get_track_pan", index=index)
    if not r.ok:
        return r
    if abs(r.value - pan) > 0.002:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (pan, r.value), wrote=pan, read=r.value)
    return ok(r.value, verified=True)
