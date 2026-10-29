import playlist


def op_playlist_inc_live_trig_mode(index: int, value: int) -> dict:
    """Run playlist.incLiveTrigMode inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value}, {"index": "i", "value": "i"})
    if bad:
        return bad
    return _run(playlist.incLiveTrigMode, index, value)
