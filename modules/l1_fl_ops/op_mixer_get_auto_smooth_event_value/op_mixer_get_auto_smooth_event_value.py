import mixer


def op_mixer_get_auto_smooth_event_value(index: int, locked: int = 1) -> dict:
    """Run mixer.getAutoSmoothEventValue inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "locked": locked}, {"index": "i", "locked": "i"})
    if bad:
        return bad
    return _run(mixer.getAutoSmoothEventValue, index, locked)
