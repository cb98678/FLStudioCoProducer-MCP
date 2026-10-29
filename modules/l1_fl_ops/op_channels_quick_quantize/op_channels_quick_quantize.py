import channels


def op_channels_quick_quantize(index: int, startOnly: int = 1, useGlobalIndex: bool = False) -> dict:
    """Run channels.quickQuantize inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "startOnly": startOnly, "useGlobalIndex": useGlobalIndex}, {"index": "i", "startOnly": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.quickQuantize, index, startOnly, useGlobalIndex)
