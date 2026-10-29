import mixer


def op_mixer_get_event_value(index: int, value: int = 0, smoothTarget: int = 1) -> dict:
    """Run mixer.getEventValue inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value, "smoothTarget": smoothTarget}, {"index": "i", "value": "i", "smoothTarget": "i"})
    if bad:
        return bad
    return _run(mixer.getEventValue, index, value, smoothTarget)
