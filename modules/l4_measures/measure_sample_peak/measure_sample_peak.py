from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_sample_peak(path: str) -> Result:
    """Measure the sample peak of an audio file in dBFS, overall and per channel."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    per = [round(dsp.db(float(v)), 2) for v in abs(x).max(axis=0)]
    return ok({"peak_db": max(per), "per_channel_db": per})
