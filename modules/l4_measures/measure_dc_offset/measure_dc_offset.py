from __future__ import annotations

import numpy as np

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_dc_offset(path: str) -> Result:
    """DC offset per channel: the whole file's mean (dc, dc_dbfs) and any held offset, a level that stays while the sound has stopped (50 ms
    frames with no motion, std under -100 dBFS): held_dbfs, held_s, first_held_s. A held offset is a stuck plugin state; it kept FL rendering
    33 s past a song's end (2026-10-25). Short-window means are not used: beat-rate kick asymmetry reads -40 dBFS in them on clean masters.
    max_dbfs is the worse of the two, for targets."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    fr = max(1, rate // 20)
    n = len(x) // fr
    blk = x[: n * fr].reshape(n, fr, -1) if n else x[None]
    std, mean = blk.std(axis=1).max(axis=1), np.abs(blk.mean(axis=1)).max(axis=1)
    held = (std < 1e-5) & (mean > 1e-4)
    dc = x.mean(axis=0)
    dc_db = dsp.db(float(np.abs(dc).max()))
    held_db = dsp.db(float(mean[held].max())) if held.any() else dsp.FLOOR_DB
    return ok({"dc": [round(float(v), 5) for v in dc], "dc_dbfs": round(dc_db, 1), "held_dbfs": round(held_db, 1),
               "held_s": round(float(held.sum()) * fr / rate, 2), "first_held_s": round(float(np.argmax(held)) * fr / rate, 2) if held.any() else None,
               "max_dbfs": round(max(dc_db, held_db), 1)})
