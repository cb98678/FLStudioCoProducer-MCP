import playlist


def op_playlist_get_live_trig_snap(index: int) -> dict:
    """Run playlist.getLiveTrigSnap inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(playlist.getLiveTrigSnap, index)
