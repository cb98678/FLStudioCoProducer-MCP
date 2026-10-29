import channels


def op_channels_get_channel_type(index: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.getChannelType inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "useGlobalIndex": useGlobalIndex}, {"index": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.getChannelType, index, useGlobalIndex)
