import mixer


def op_mixer_solo_track(index: int, value: int = -1, mode: int = -1) -> dict:
    """Run mixer.soloTrack inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value, "mode": mode}, {"index": "i", "value": "j", "mode": "j"})
    if bad:
        return bad
    return _run(mixer.soloTrack, index, value, mode)
