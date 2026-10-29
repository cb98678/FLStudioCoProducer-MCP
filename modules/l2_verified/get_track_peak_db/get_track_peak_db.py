from __future__ import annotations

import math

from coproducer import call
from coproducer.result import Result, ok


def get_track_peak_db(index: int) -> Result:
    """Return a mixer track's current peak (max of left and right) as a linear value and in dBFS.

    FL only updates peaks while audio plays. Silence reads as -120 dB.
    """
    r = call("op_mixer_get_track_peaks", index=index, mode=2)
    if not r.ok:
        return r
    db = 20 * math.log10(r.value) if r.value > 1e-6 else -120.0
    return ok({"linear": r.value, "db": round(db, 2)})
