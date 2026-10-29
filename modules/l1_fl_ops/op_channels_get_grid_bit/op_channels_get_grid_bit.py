import channels


def op_channels_get_grid_bit(index: int, position: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.getGridBit inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "position": position, "useGlobalIndex": useGlobalIndex}, {"index": "i", "position": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.getGridBit, index, position, useGlobalIndex)
