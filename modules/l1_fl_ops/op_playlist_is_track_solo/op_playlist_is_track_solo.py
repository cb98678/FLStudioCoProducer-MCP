import playlist


def op_playlist_is_track_solo(index: int) -> dict:
    """Run playlist.isTrackSolo inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(playlist.isTrackSolo, index)
