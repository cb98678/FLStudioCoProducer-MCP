import mixer


def op_mixer_get_track_pan(index: int) -> dict:
    """Run mixer.getTrackPan inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(mixer.getTrackPan, index)
