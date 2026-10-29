from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_route_level_verified(index: int, dest_index: int, level: float) -> Result:
    """Set the send level from one mixer track to another (0.0 to 1.0) and confirm it.

    Errors: E_ARG for bad input or an FL-side failure, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_mixer_set_route_to_level", index=index, destIndex=dest_index, level=level)
    if not w.ok:
        return w
    r = call("op_mixer_get_route_to_level", index=index, destIndex=dest_index)
    if not r.ok:
        return r
    if abs(r.value - level) > 0.002:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (level, r.value), wrote=level, read=r.value)
    return ok(r.value, verified=True)
