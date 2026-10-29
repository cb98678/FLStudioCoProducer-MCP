from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_rms(path: str) -> Result:
    """Measure the RMS level of an audio file in dBFS, overall and per channel."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    per = [round(dsp.db(float((x[:, c] ** 2).mean() ** 0.5)), 2) for c in range(x.shape[1])]
    return ok({"rms_db": round(dsp.db(float((x ** 2).mean() ** 0.5)), 2), "per_channel_db": per})
