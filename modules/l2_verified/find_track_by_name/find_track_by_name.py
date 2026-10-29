from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok


def find_track_by_name(pattern: str, ignore_case: bool = True) -> Result:
    """Return the indexes and names of mixer tracks whose name contains pattern.

    Errors: any read error while scanning names.
    """
    n = call("op_mixer_track_count")
    if not n.ok:
        return n
    want = pattern.lower() if ignore_case else pattern
    hits = []
    for i in range(n.value):
        r = call("op_mixer_get_track_name", index=i)
        if not r.ok:
            return r
        if want in (r.value.lower() if ignore_case else r.value):
            hits.append({"index": i, "name": r.value})
    return ok(hits)
