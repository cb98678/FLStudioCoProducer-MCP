from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def solo_track_verified(index: int, solo: bool) -> Result:
    """Set a mixer track's solo state to an explicit value and confirm it.

    Errors: E_ARG for bad input or an FL-side failure, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_mixer_solo_track", index=index, value=1 if solo else 0)
    if not w.ok:
        return w
    r = call("op_mixer_is_track_solo", index=index)
    if not r.ok:
        return r
    if r.value != solo:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (solo, r.value), wrote=solo, read=r.value)
    return ok(r.value, verified=True)
