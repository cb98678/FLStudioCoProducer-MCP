from __future__ import annotations

import numpy as np

from coproducer import dsp
from coproducer.result import Result, fail, ok


def count_clipped_samples(path: str, threshold: float = 0.9999) -> Result:
    """Count samples at or beyond a clipping threshold and report the longest run of consecutive clipped samples."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    hit = abs(x) >= threshold
    longest = 0
    for c in range(x.shape[1]):
        edges = np.diff(np.r_[0, hit[:, c].astype(int), 0])
        runs = np.where(edges == -1)[0] - np.where(edges == 1)[0]
        longest = max(longest, int(runs.max()) if len(runs) else 0)
    return ok({"clipped_samples": int(hit.sum()), "longest_run": longest, "clipped_fraction": round(float(hit.mean()), 6)})
