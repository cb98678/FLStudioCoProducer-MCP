import channels


def op_channels_select_one_channel(index: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.selectOneChannel inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "useGlobalIndex": useGlobalIndex}, {"index": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.selectOneChannel, index, useGlobalIndex)
