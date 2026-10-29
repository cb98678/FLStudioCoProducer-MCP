import channels


def op_channels_is_channel_muted(index: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.isChannelMuted inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "useGlobalIndex": useGlobalIndex}, {"index": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.isChannelMuted, index, useGlobalIndex)
