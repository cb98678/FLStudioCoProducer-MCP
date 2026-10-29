import mixer


def op_mixer_link_track_to_channel(mode: int) -> dict:
    """Run mixer.linkTrackToChannel inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"mode": mode}, {"mode": "i"})
    if bad:
        return bad
    return _run(mixer.linkTrackToChannel, mode)
