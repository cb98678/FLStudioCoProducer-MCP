import mixer


def op_mixer_get_track_info(mode: int) -> dict:
    """Run mixer.getTrackInfo inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"mode": mode}, {"mode": "i"})
    if bad:
        return bad
    return _run(mixer.getTrackInfo, mode)
