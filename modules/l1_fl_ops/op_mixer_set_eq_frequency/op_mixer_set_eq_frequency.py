import mixer


def op_mixer_set_eq_frequency(index: int, band: int, value: float) -> dict:
    """Run mixer.setEqFrequency inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "band": band, "value": value}, {"index": "i", "band": "i", "value": "n"})
    if bad:
        return bad
    return _run(mixer.setEqFrequency, index, band, value)
