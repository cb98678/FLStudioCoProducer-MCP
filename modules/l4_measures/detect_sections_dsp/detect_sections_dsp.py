from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def detect_sections_dsp(path: str, min_len_s: float = 8.0) -> Result:
    """Estimate section boundaries (intro, build, drop and so on) from changes in the spectrum over time.

    Returns boundary times in seconds with a strength. Needs at least 30 seconds of audio.
    """
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    if x.shape[0] / rate < 30.0:
        return fail("E_ARG", "at least 30 seconds of audio are needed")
    marks = dsp.section_boundaries(x, rate, min_len_s)
    return ok({"boundaries": marks, "sections": len(marks) + 1})
