import transport


def op_transport_set_playback_speed(speedMultiplier: float) -> dict:
    """Run transport.setPlaybackSpeed inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"speedMultiplier": speedMultiplier}, {"speedMultiplier": "n"})
    if bad:
        return bad
    return _run(transport.setPlaybackSpeed, speedMultiplier)
