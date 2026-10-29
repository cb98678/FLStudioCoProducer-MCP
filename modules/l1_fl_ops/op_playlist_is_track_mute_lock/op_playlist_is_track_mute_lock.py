import playlist


def op_playlist_is_track_mute_lock(index: int) -> dict:
    """Run playlist.isTrackMuteLock inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(playlist.isTrackMuteLock, index)
