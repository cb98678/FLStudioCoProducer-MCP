from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok


def restore_solo_group(previous: dict) -> Result:
    """Put mixer track solo states back to the map returned by solo_group (track index text to bool).

    Errors: the first verified-write failure.
    """
    for key, state in previous.items():
        r = call("solo_track_verified", index=int(key), solo=bool(state))
        if not r.ok:
            return r
    return ok({"restored": len(previous)}, verified=True)
