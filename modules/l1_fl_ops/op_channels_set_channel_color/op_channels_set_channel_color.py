import channels


def op_channels_set_channel_color(index: int, color: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.setChannelColor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "color": color, "useGlobalIndex": useGlobalIndex}, {"index": "i", "color": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.setChannelColor, index, color, useGlobalIndex)
