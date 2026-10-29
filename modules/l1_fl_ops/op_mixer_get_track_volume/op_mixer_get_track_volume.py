import mixer


def op_mixer_get_track_volume(index: int, mode: int = 0) -> dict:
    """Run mixer.getTrackVolume inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "mode": mode}, {"index": "i", "mode": "i"})
    if bad:
        return bad
    return _run(mixer.getTrackVolume, index, mode)
