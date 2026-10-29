from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_spectral_centroid(path: str) -> Result:
    """Measure the spectral centroid (brightness) of an audio file in Hz."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    return ok({"centroid_hz": round(dsp.spectral_centroid(x, rate), 1)})
