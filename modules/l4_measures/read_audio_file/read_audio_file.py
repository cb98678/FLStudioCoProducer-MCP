from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def read_audio_file(path: str, max_seconds: float = 0.0) -> Result:
    """Load an audio file as a float array with its sample rate. max_seconds 0 reads the whole file."""
    try:
        x, rate = dsp.load_audio(path, max_seconds)
    except ValueError as e:
        return fail("E_IO", str(e))
    return ok({"samples": x, "rate": rate, "channels": x.shape[1], "seconds": round(x.shape[0] / rate, 3)})
