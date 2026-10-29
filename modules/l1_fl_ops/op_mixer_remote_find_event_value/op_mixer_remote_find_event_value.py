import mixer


def op_mixer_remote_find_event_value(index: int, flags: int = 0) -> dict:
    """Run mixer.remoteFindEventValue inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "flags": flags}, {"index": "i", "flags": "i"})
    if bad:
        return bad
    return _run(mixer.remoteFindEventValue, index, flags)
