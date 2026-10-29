import channels


def op_channels_mute_channel(index: int, value: int = -1, useGlobalIndex: bool = False) -> dict:
    """Run channels.muteChannel inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value, "useGlobalIndex": useGlobalIndex}, {"index": "i", "value": "j", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.muteChannel, index, value, useGlobalIndex)
