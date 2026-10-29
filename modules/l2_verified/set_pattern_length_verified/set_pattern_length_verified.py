from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def set_pattern_length_verified(index: int, length: int) -> Result:
    """Set a pattern's length and confirm by reading it back, in the same unit getPatternLength reports.

    Measured on FL 26.1.7: setPatternLength(1, 8) reads back 8 and incrementPatternLength changes it by the
    given amount. Errors: E_ARG when FL rejects the arguments, E_NOT_VERIFIED when the readback differs.
    """
    w = call("op_patterns_set_pattern_length", index=index, length=length)
    if not w.ok:
        return w
    r = call("op_patterns_get_pattern_length", index=index)
    if not r.ok:
        return r
    if r.value != length:
        return fail("E_NOT_VERIFIED", "wrote %r but read back %r" % (length, r.value), wrote=length, read=r.value)
    return ok(r.value, verified=True)
