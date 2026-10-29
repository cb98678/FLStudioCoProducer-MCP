import playlist


def op_playlist_lock_display_zone(index: int, value: int) -> dict:
    """Run playlist.lockDisplayZone inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value}, {"index": "i", "value": "i"})
    if bad:
        return bad
    return _run(playlist.lockDisplayZone, index, value)
