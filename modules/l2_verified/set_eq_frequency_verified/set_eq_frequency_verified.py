from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_eq_frequency_verified(index: int, band: int, value: float) -> Result:
    """Set one mixer EQ band's frequency (0.0 to 1.0, normalized) and confirm it.

    Errors: E_ARG for bad input or an FL-side failure, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_mixer_set_eq_frequency", index=index, band=band, value=value)
    if not w.ok:
        return w
    r = call("op_mixer_get_eq_frequency", index=index, band=band)
    if not r.ok:
        return r
    if abs(r.value - value) > 0.002:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (value, r.value), wrote=value, read=r.value)
    return ok(r.value, verified=True)
