from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_mid_side_ratio(path: str) -> Result:
    """Measure the mid to side energy ratio of a stereo file in dB."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    if x.shape[1] < 2:
        return fail("E_ARG", "a stereo file is needed")
    mid, side = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    m, s = float((mid ** 2).mean()), float((side ** 2).mean())
    return ok({"mid_side_db": round(dsp.power_db(m) - dsp.power_db(s), 2), "mono": s < 1e-12})
