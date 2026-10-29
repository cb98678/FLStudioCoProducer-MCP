import mixer


def op_mixer_get_track_peaks(index: int, mode: int) -> dict:
    """Run mixer.getTrackPeaks inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "mode": mode}, {"index": "i", "mode": "i"})
    if bad:
        return bad
    return _run(mixer.getTrackPeaks, index, mode)
