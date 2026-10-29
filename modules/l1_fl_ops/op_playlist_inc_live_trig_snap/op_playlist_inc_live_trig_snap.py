import playlist


def op_playlist_inc_live_trig_snap(index: int, value: int) -> dict:
    """Run playlist.incLiveTrigSnap inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value}, {"index": "i", "value": "i"})
    if bad:
        return bad
    return _run(playlist.incLiveTrigSnap, index, value)
