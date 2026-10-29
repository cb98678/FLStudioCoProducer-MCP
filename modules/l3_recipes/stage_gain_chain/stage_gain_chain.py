from __future__ import annotations

import time

from coproducer import call
from coproducer.result import Result, ok


def _held_peak_db(index: int, hold_s: float) -> Result:
    deadline, best = time.monotonic() + hold_s, None
    while True:
        r = call("get_track_peak_db", index=index)
        if not r.ok:
            return r
        best = r.value["db"] if best is None else max(best, r.value["db"])
        if time.monotonic() >= deadline:
            return ok(best)
        time.sleep(0.05)


def stage_gain_chain(stages: list[dict], hold_s: float = 1.0, max_delta_db: float = 6.0) -> Result:
    """Walk gain stages in order. For each, hold the peak meter for hold_s seconds, then trim the fader toward its target peak.

    Audio must be playing. A stage whose meter reads silence is skipped and reported, not changed.
    """
    report = []
    for st in stages:
        peak = _held_peak_db(st["index"], hold_s)
        if not peak.ok:
            return peak
        if peak.value <= -100.0:
            report.append({"index": st["index"], "skipped": "silent"})
            continue
        r = call("apply_gain_trim", index=st["index"], delta_db=st["target_peak_db"] - peak.value, max_delta_db=max_delta_db)
        if not r.ok:
            return r
        report.append({"index": st["index"], "peak_db": peak.value, **r.value})
    return ok({"stages": report}, verified=True)
