import playlist


def op_playlist_is_track_selected(index: int) -> dict:
    """Run playlist.isTrackSelected inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(playlist.isTrackSelected, index)
