import playlist


def op_playlist_solo_track(index: int, value: int = -1, inGroup: bool = False) -> dict:
    """Run playlist.soloTrack inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value, "inGroup": inGroup}, {"index": "i", "value": "j", "inGroup": "b"})
    if bad:
        return bad
    return _run(playlist.soloTrack, index, value, inGroup)
