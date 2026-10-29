import channels


def op_channels_is_channel_selected(index: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.isChannelSelected inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "useGlobalIndex": useGlobalIndex}, {"index": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.isChannelSelected, index, useGlobalIndex)
