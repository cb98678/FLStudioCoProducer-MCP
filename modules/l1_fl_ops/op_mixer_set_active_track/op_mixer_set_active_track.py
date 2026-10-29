import mixer


def op_mixer_set_active_track(index: int) -> dict:
    """Run mixer.setActiveTrack inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(mixer.setActiveTrack, index)
