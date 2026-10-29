from __future__ import annotations

from coproducer import call
from coproducer.result import Result, ok


def apply_eq_recipe(index: int, bands: list[dict]) -> Result:
    """Apply EQ settings to a mixer track. Each band dict has band (0 to 2) plus any of gain, freq, bandwidth (0 to 1).

    Every value is written through a verified setter. Errors: the first failing write.
    """
    steps = []
    for b in bands:
        if "gain" in b:
            steps.append(lambda b=b: call("set_eq_gain_verified", index=index, band=b["band"], value=b["gain"]))
        if "freq" in b:
            steps.append(lambda b=b: call("set_eq_frequency_verified", index=index, band=b["band"], value=b["freq"]))
        if "bandwidth" in b:
            steps.append(lambda b=b: call("set_eq_bandwidth_verified", index=index, band=b["band"], value=b["bandwidth"]))
    for step in steps:
        r = step()
        if not r.ok:
            return r
    done = len(steps)
    return ok({"values_set": done}, verified=True)
