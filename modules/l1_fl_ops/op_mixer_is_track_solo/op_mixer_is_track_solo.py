import mixer


def op_mixer_is_track_solo(index: int) -> dict:
    """Run mixer.isTrackSolo inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(mixer.isTrackSolo, index)
