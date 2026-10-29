import playlist


def op_playlist_mute_track(index: int, value: int = -1) -> dict:
    """Run playlist.muteTrack inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value}, {"index": "i", "value": "j"})
    if bad:
        return bad
    return _run(playlist.muteTrack, index, value)
