import playlist


def op_playlist_select_track(index: int) -> dict:
    """Run playlist.selectTrack inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(playlist.selectTrack, index)
