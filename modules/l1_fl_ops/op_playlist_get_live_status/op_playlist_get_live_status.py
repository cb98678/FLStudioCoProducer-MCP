import playlist


def op_playlist_get_live_status(index: int, mode: int = 0) -> dict:
    """Run playlist.getLiveStatus inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "mode": mode}, {"index": "i", "mode": "i"})
    if bad:
        return bad
    return _run(playlist.getLiveStatus, index, mode)
