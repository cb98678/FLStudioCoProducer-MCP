import channels


def op_channels_get_channel_volume(index: int, mode: bool = False, useGlobalIndex: bool = False) -> dict:
    """Run channels.getChannelVolume inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "mode": mode, "useGlobalIndex": useGlobalIndex}, {"index": "i", "mode": "b", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.getChannelVolume, index, mode, useGlobalIndex)
