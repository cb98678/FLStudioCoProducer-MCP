from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok


def solo_group(indexes: list[int]) -> Result:
    """Solo the listed mixer tracks and un-solo every other track. The value holds the previous solo states.

    Pass that value to restore_solo_group to undo it.
    """
    n = call("op_mixer_track_count")
    if not n.ok:
        return n
    previous = {}
    for i in range(n.value):
        cur = call("op_mixer_is_track_solo", index=i)
        if not cur.ok:
            return cur
        previous[str(i)] = cur.value
        if cur.value != (i in indexes):
            r = call("solo_track_verified", index=i, solo=i in indexes)
            if not r.ok:
                return r
    return ok({"previous": previous}, verified=True)
