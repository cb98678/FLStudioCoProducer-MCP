import mixer


def op_mixer_is_track_armed(index: int) -> dict:
    """Run mixer.isTrackArmed inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(mixer.isTrackArmed, index)
