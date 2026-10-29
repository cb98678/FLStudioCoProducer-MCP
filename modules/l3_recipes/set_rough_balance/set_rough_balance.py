from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok


def set_rough_balance(levels_db: dict) -> Result:
    """Set starting fader levels for many mixer tracks. levels_db maps track index text to a level in dB.

    Errors: the first track whose level cannot be set and verified.
    """
    achieved = {}
    for key, db in levels_db.items():
        r = call("set_track_volume_db_verified", index=int(key), db=db)
        if not r.ok:
            return r
        achieved[key] = r.value
    return ok({"achieved_db": achieved}, verified=True)
