import mixer


def op_mixer_is_track_plugin_valid(index: int, plugIndex: int) -> dict:
    """Run mixer.isTrackPluginValid inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "plugIndex": plugIndex}, {"index": "i", "plugIndex": "i"})
    if bad:
        return bad
    return _run(mixer.isTrackPluginValid, index, plugIndex)
