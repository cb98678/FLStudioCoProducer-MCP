import playlist


def op_playlist_trigger_live_clip(index: int, subNum: int, flags: int, velocity: int = -1) -> dict:
    """Run playlist.triggerLiveClip inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "subNum": subNum, "flags": flags, "velocity": velocity}, {"index": "i", "subNum": "i", "flags": "i", "velocity": "j"})
    if bad:
        return bad
    return _run(playlist.triggerLiveClip, index, subNum, flags, velocity)
