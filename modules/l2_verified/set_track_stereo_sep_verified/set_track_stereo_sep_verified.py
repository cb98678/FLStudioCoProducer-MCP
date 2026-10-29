from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_track_stereo_sep_verified(index: int, separation: float) -> Result:
    """Set a mixer track's stereo separation from -1.0 to 1.0 and confirm by reading it back.

    Errors: E_ARG for bad input or an FL-side failure, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_mixer_set_track_stereo_sep", index=index, pan=separation)
    if not w.ok:
        return w
    r = call("op_mixer_get_track_stereo_sep", index=index)
    if not r.ok:
        return r
    if abs(r.value - separation) > 0.002:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (separation, r.value), wrote=separation, read=r.value)
    return ok(r.value, verified=True)
