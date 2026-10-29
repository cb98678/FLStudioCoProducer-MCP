from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def detect_leakage(path: str, others: list[str]) -> Result:
    """Estimate how much of a stem's power is linearly predictable from each of the other files (its leakage).

    Each entry gives the share (0 to 1) and the level in dB below the stem. High shares mean the stem is not clean.
    """
    try:
        stem, rate = dsp.load_audio(path)
        found = [(p, *dsp.load_audio(p)) for p in others]
    except ValueError as e:
        return fail("E_IO", str(e))
    rows = []
    for p, other, other_rate in found:
        if other_rate != rate:
            return fail("E_ARG", "%s has sample rate %d, the stem has %d" % (p, other_rate, rate))
        share = dsp.leakage_fraction(stem, other, rate)
        rows.append({"source": p, "share": round(share, 4), "db": round(dsp.power_db(share), 1)})
    return ok({"leakage": rows, "worst_share": max((r["share"] for r in rows), default=0.0)})
