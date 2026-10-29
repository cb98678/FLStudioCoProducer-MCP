import mixer


def op_mixer_enable_track(index: int) -> dict:
    """Run mixer.enableTrack inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(mixer.enableTrack, index)
