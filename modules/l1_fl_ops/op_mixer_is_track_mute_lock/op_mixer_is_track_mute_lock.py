import mixer


def op_mixer_is_track_mute_lock(index: int) -> dict:
    """Run mixer.isTrackMuteLock inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(mixer.isTrackMuteLock, index)
