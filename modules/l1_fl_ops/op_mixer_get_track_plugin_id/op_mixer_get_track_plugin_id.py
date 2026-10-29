import mixer


def op_mixer_get_track_plugin_id(index: int, plugIndex: int) -> dict:
    """Run mixer.getTrackPluginId inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "plugIndex": plugIndex}, {"index": "i", "plugIndex": "i"})
    if bad:
        return bad
    return _run(mixer.getTrackPluginId, index, plugIndex)
