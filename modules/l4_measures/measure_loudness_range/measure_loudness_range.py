from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_loudness_range(path: str) -> Result:
    """Measure loudness range (LRA) in LU per EBU Tech 3342 from short-term loudness."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    _, lufs = dsp.window_loudness(x, rate, 3.0, 0.1)
    if len(lufs) == 0:
        return fail("E_ARG", "audio is shorter than the 3 second window")
    lra, lo, hi = dsp.loudness_range(lufs)
    return ok({"lra_lu": round(lra, 2), "low_lufs": round(lo, 2), "high_lufs": round(hi, 2)})
