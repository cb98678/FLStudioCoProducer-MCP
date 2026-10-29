from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def estimate_key_dsp(path: str) -> Result:
    """Estimate the musical key from audio with chroma and Krumhansl-Schmuckler profiles.

    margin is the score gap to the runner-up; below about 0.05 treat the key as uncertain. Works best on tonal material.
    """
    try:
        x, rate = dsp.load_audio(path, 120.0)
    except ValueError as e:
        return fail("E_IO", str(e))
    return ok(dsp.estimate_key(x, rate))
