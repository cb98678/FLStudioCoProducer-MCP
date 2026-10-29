from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_short_term_loudness(path: str, hop_s: float = 1.0) -> Result:
    """Measure short-term loudness (3 second window) over time in LUFS."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    t, lufs = dsp.window_loudness(x, rate, 3.0, hop_s)
    if len(lufs) == 0:
        return fail("E_ARG", "audio is shorter than the 3 second window")
    return ok({"times_s": [round(float(v), 2) for v in t], "lufs": [round(float(v), 2) for v in lufs],
               "max_lufs": round(float(lufs.max()), 2), "min_lufs": round(float(lufs.min()), 2)})
