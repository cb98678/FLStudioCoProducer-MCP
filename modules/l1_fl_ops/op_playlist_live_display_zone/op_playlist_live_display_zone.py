import playlist


def op_playlist_live_display_zone(left: int, top: int, right: int, bottom: int, duration: int = 0) -> dict:
    """Run playlist.liveDisplayZone inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"left": left, "top": top, "right": right, "bottom": bottom, "duration": duration}, {"left": "i", "top": "i", "right": "i", "bottom": "i", "duration": "i"})
    if bad:
        return bad
    return _run(playlist.liveDisplayZone, left, top, right, bottom, duration)
