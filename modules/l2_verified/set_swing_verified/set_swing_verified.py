from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_swing_verified(swing: float) -> Result:
    """Set the global channel swing from 0.0 to 1.0 and confirm by reading it back.

    The scale is assumed to be 0.0 to 1.0 (a fresh project reads 0.0); the readback check fails safe if FL
    stores it differently. Errors: E_ARG when FL rejects the value, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_channels_set_swing", value=swing)
    if not w.ok:
        return w
    r = call("op_channels_get_swing")
    if not r.ok:
        return r
    if abs(r.value - swing) > 0.005:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (swing, r.value), wrote=swing, read=r.value)
    return ok(r.value, verified=True)
