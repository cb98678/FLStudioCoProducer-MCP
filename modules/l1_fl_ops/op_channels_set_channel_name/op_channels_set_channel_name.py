import channels


def op_channels_set_channel_name(index: int, name: str, useGlobalIndex: bool = False) -> dict:
    """Run channels.setChannelName inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "name": name, "useGlobalIndex": useGlobalIndex}, {"index": "i", "name": "s", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.setChannelName, index, name, useGlobalIndex)
