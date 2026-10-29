import mixer


def op_mixer_get_eq_bandwidth(index: int, band: int) -> dict:
    """Run mixer.getEqBandwidth inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "band": band}, {"index": "i", "band": "i"})
    if bad:
        return bad
    return _run(mixer.getEqBandwidth, index, band)
