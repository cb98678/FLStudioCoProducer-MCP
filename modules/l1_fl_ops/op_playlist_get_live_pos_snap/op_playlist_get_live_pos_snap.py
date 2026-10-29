import playlist


def op_playlist_get_live_pos_snap(index: int) -> dict:
    """Run playlist.getLivePosSnap inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(playlist.getLivePosSnap, index)
