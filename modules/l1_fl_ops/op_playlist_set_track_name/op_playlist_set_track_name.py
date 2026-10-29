import playlist


def op_playlist_set_track_name(index: int, name: str) -> dict:
    """Run playlist.setTrackName inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "name": name}, {"index": "i", "name": "s"})
    if bad:
        return bad
    return _run(playlist.setTrackName, index, name)
