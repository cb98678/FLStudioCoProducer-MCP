from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_masking_overlap(path_a: str, path_b: str) -> Result:
    """Estimate, band by band, how much two audio files compete for the same frequencies, from 0 to 1.

    1 means both have similar energy in the band. The worst three bands are listed first.
    """
    try:
        a, rate_a = dsp.load_audio(path_a)
        b, rate_b = dsp.load_audio(path_b)
    except ValueError as e:
        return fail("E_IO", str(e))
    if rate_a != rate_b:
        return fail("E_ARG", "the files have different sample rates: %d and %d" % (rate_a, rate_b))
    bands = dsp.band_overlap(a, b, rate_a, dsp.DEFAULT_BANDS)
    worst = sorted(bands, key=lambda k: -bands[k])[:3]
    return ok({"bands": bands, "worst": [{"band": k, "overlap": bands[k]} for k in worst if bands[k] > 0]})
