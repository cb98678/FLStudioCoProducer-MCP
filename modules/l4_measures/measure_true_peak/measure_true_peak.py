from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_true_peak(path: str, oversample: int = 4) -> Result:
    """Measure the true peak of an audio file in dBTP using oversampling, and flag intersample overs."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    tp, sp = dsp.true_peak(x, rate, oversample), float(abs(x).max())
    return ok({"true_peak_dbtp": round(dsp.db(tp), 2), "sample_peak_db": round(dsp.db(sp), 2),
               "intersample_over": tp > 1.0 and sp <= 1.0})
