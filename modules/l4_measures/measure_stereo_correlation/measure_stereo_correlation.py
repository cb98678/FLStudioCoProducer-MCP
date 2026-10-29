from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_stereo_correlation(path: str) -> Result:
    """Measure the stereo correlation coefficient of a stereo file, from -1 to 1."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    if x.shape[1] < 2:
        return fail("E_ARG", "a stereo file is needed")
    c = dsp.correlation(x[:, 0], x[:, 1])
    return ok({"correlation": round(c, 3), "mono_compatible": c > 0.0})
