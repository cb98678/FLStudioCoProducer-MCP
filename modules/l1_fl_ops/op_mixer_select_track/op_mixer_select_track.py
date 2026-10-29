import mixer


def op_mixer_select_track(index: int) -> dict:
    """Run mixer.selectTrack inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(mixer.selectTrack, index)
