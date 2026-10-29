from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_crest_factor(path: str) -> Result:
    """Measure the crest factor (peak to RMS ratio) of an audio file in dB."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    peak, rms = dsp.db(float(abs(x).max())), dsp.db(float((x ** 2).mean() ** 0.5))
    return ok({"crest_db": round(peak - rms, 2), "peak_db": round(peak, 2), "rms_db": round(rms, 2)})
