from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_integrated_loudness(path: str) -> Result:
    """Measure integrated loudness in LUFS per ITU-R BS.1770-4 with EBU R128 gating."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    try:
        lufs = dsp.integrated_loudness(x, rate)
    except ValueError as e:
        return fail("E_ARG", str(e))
    return ok({"lufs": round(lufs, 2)})
