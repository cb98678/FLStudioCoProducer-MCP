from __future__ import annotations

from coproducer import call
from coproducer.result import Result, fail, ok


def add_time_marker_verified(time: int, name: str) -> Result:
    """Add a named time marker to the arrangement at a tick position and confirm it exists.

    Confirmation scans up to 128 marker names for the new name. Errors: E_NOT_VERIFIED when it is not found.
    """
    w = call("op_arrangement_add_auto_time_marker", time=time, name=name)
    if not w.ok:
        return w
    for i in range(128):
        r = call("op_arrangement_get_marker_name", index=i)
        if not r.ok:
            break
        if r.value == name:
            return ok(i, verified=True)
    return fail("E_NOT_VERIFIED", "marker %r was not found after adding it" % name)
