import mixer


def op_mixer_enable_track_slots(index: int, value: bool = False) -> dict:
    """Run mixer.enableTrackSlots inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value}, {"index": "i", "value": "b"})
    if bad:
        return bad
    return _run(mixer.enableTrackSlots, index, value)
