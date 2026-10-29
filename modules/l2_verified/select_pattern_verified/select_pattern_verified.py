from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def select_pattern_verified(index: int) -> Result:
    """Make a pattern current and confirm by reading the current pattern number.

    Errors: E_ARG for bad input or an FL-side failure, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_patterns_jump_to_pattern", index=index)
    if not w.ok:
        return w
    r = call("op_patterns_pattern_number")
    if not r.ok:
        return r
    if r.value != index:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (index, r.value), wrote=index, read=r.value)
    return ok(r.value, verified=True)
