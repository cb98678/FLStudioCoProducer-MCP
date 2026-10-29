from __future__ import annotations

from coproducer import cutrefine, dsp
from coproducer.result import Result, fail, ok


def find_final_s_end(path: str, end_s: float, reach_s: float = 0.45) -> Result:
    """Where a vocal cut ending at end_s should really end if its last word closes on an s or z (blues, places, friends).

    Looks for the first hiss within reach_s after end_s (4 to 12 kHz burst that is not a bright vowel) and returns the time just after it, at the dip in front
    of the next word. If a hiss already ended just before end_s, or none follows, the end is returned unchanged (found is false). The caller decides whether
    the word needs an s (cutrefine.wants_final_s does it from spelling); this module only reads the signal.
    """
    start = max(0.0, end_s - 0.3)
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    if end_s >= x.shape[0] / rate:
        return fail("E_ARG", "end_s is past the end of the file")
    seg = x[int(start * rate) : int((end_s + reach_s + 0.2) * rate)].mean(axis=1)
    new = cutrefine.final_s(seg, rate, end_s - start, reach=reach_s) + start
    return ok({"end_s": round(float(new), 3), "moved_s": round(float(new - end_s), 3), "found": bool(new > end_s + 1e-6)})
