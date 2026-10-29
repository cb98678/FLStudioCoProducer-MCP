import channels


def op_channels_get_channel_pan(index: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.getChannelPan inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "useGlobalIndex": useGlobalIndex}, {"index": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.getChannelPan, index, useGlobalIndex)
