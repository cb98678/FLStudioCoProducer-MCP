import channels


def op_channels_select_channel(index: int, value: int = -1, useGlobalIndex: bool = False) -> dict:
    """Run channels.selectChannel inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value, "useGlobalIndex": useGlobalIndex}, {"index": "i", "value": "j", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.selectChannel, index, value, useGlobalIndex)
