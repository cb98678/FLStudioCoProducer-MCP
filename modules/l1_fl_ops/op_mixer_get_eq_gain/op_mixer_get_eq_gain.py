import mixer


def op_mixer_get_eq_gain(index: int, band: int, mode: int = 0) -> dict:
    """Run mixer.getEqGain inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "band": band, "mode": mode}, {"index": "i", "band": "i", "mode": "i"})
    if bad:
        return bad
    return _run(mixer.getEqGain, index, band, mode)
