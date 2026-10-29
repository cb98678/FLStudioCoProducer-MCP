import playlist


def op_playlist_get_track_activity_level_vis(index: int) -> dict:
    """Run playlist.getTrackActivityLevelVis inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(playlist.getTrackActivityLevelVis, index)
