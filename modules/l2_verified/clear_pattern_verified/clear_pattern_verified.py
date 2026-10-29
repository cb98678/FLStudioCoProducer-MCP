from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def clear_pattern_verified(index: int) -> Result:
    """Clear a pattern and confirm that FL now reports it as default (empty).

    Measured on FL 26.1.7: isPatternDefault is 1 for an untouched pattern and 0 once it has step data, and
    clearPattern on a pattern that has data opens a confirmation dialog in FL that blocks the bridge until someone
    clicks OK (or ticks Remember my choice). An already empty pattern is left alone and needs no dialog.
    Errors: E_ARG when FL rejects the index, E_TIMEOUT while the dialog waits, E_NOT_VERIFIED when it is still not default.
    """
    before = call("op_patterns_is_pattern_default", index=index)
    if not before.ok:
        return before
    if before.value:
        return ok({"cleared": False, "was_empty": True}, verified=True)
    w = call("op_patterns_clear_pattern", index=index)
    if not w.ok:
        return w
    after = call("op_patterns_is_pattern_default", index=index)
    if not after.ok:
        return after
    if not after.value:
        return fail("E_NOT_VERIFIED", "pattern %d is still not default after clearPattern" % index, index=index)
    return ok({"cleared": True, "was_empty": False}, verified=True)
