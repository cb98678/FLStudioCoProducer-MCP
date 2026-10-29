import mixer


def op_mixer_get_eq_frequency(index: int, band: int, mode: int = 0) -> dict:
    """Run mixer.getEqFrequency inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "band": band, "mode": mode}, {"index": "i", "band": "i", "mode": "i"})
    if bad:
        return bad
    return _run(mixer.getEqFrequency, index, band, mode)
