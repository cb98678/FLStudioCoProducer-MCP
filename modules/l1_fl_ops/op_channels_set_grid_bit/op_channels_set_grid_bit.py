import channels


def op_channels_set_grid_bit(index: int, position: int, value: bool, useGlobalIndex: bool = False) -> dict:
    """Run channels.setGridBit inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "position": position, "value": value, "useGlobalIndex": useGlobalIndex}, {"index": "i", "position": "i", "value": "b", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.setGridBit, index, position, value, useGlobalIndex)
