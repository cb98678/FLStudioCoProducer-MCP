from __future__ import annotations

import numpy as np

from coproducer import dsp
from coproducer.result import Result, fail, ok


def detect_silence(path: str, threshold_db: float = -60.0, min_len_s: float = 0.5) -> Result:
    """Find silent regions (RMS below threshold_db for at least min_len_s) and report how silent the file is.

    mostly_silent is true when more than 90 percent of the file is silent; duration_s is the length that was read.
    """
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    frame = max(1, rate // 100)
    n = x.shape[0] // frame
    rms = np.sqrt((x[: n * frame].reshape(n, frame, -1) ** 2).mean(axis=(1, 2)))
    quiet = np.r_[0, (rms < 10 ** (threshold_db / 20)).astype(int), 0]
    edges = np.diff(quiet)
    starts, ends = np.where(edges == 1)[0], np.where(edges == -1)[0]
    regions = [{"start_s": round(s * frame / rate, 2), "end_s": round(e * frame / rate, 2)}
               for s, e in zip(starts, ends) if (e - s) * frame / rate >= min_len_s]
    silent_s = sum(r["end_s"] - r["start_s"] for r in regions)
    total = n * frame / rate
    return ok({"regions": regions, "silent_fraction": round(silent_s / total, 3) if total else 1.0,
               "mostly_silent": bool(total == 0 or silent_s / total > 0.9), "duration_s": round(x.shape[0] / rate, 3)})
