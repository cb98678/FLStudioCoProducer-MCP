from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok

FADER_TOP_DB = 5.5       # FL's mixer fader tops out at +5.59 dB (measured on FL 26.1.7); stay just under it


def apply_gain_trim(index: int, delta_db: float, max_delta_db: float = 6.0) -> Result:
    """Change a mixer track's fader by delta_db, capped at max_delta_db and at the fader's top, and confirm in dB.

    The caller measures the audio and decides delta_db; this recipe only applies a safe, capped step.
    """
    cur = call("op_mixer_get_track_volume", index=index, mode=1)
    if not cur.ok:
        return cur
    step = max(-max_delta_db, min(max_delta_db, delta_db))
    applied = min(step, FADER_TOP_DB - cur.value) if cur.value != float("-inf") else step
    r = call("set_track_volume_db_verified", index=index, db=cur.value + applied)
    if not r.ok:
        return r
    return ok({"before_db": cur.value, "after_db": r.value, "requested_delta_db": delta_db,
               "applied_delta_db": applied, "capped": abs(applied - delta_db) > 1e-9}, verified=True)
