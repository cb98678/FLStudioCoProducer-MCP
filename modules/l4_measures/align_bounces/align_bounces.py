from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def align_bounces(path_a: str, path_b: str, max_lag_s: float = 1.0) -> Result:
    """Find the delay that best aligns bounce B to bounce A by cross-correlation.

    A positive lag means B starts late. correlation near 1 means a good match.
    """
    try:
        a, rate_a = dsp.load_audio(path_a, 120.0)
        b, rate_b = dsp.load_audio(path_b, 120.0)
    except ValueError as e:
        return fail("E_IO", str(e))
    if rate_a != rate_b:
        return fail("E_ARG", "the files have different sample rates: %d and %d" % (rate_a, rate_b))
    lag, corr = dsp.best_lag(dsp.mono(a), dsp.mono(b), int(max_lag_s * rate_a))
    return ok({"lag_samples": lag, "lag_s": round(lag / rate_a, 5), "correlation": round(corr, 4)})
