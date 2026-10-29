import mixer


def op_mixer_rev_track_polarity(index: int, value: bool = False) -> dict:
    """Run mixer.revTrackPolarity inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value}, {"index": "i", "value": "b"})
    if bad:
        return bad
    return _run(mixer.revTrackPolarity, index, value)
