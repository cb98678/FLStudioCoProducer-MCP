import playlist


def op_playlist_mute_track_lock(index: int) -> dict:
    """Run playlist.muteTrackLock inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(playlist.muteTrackLock, index)
