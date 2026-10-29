import mixer


def op_mixer_is_track_enabled(index: int) -> dict:
    """Run mixer.isTrackEnabled inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(mixer.isTrackEnabled, index)
