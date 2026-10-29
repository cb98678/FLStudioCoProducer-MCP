import channels


def op_channels_get_grid_bit_with_loop(index: int, position: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.getGridBitWithLoop inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "position": position, "useGlobalIndex": useGlobalIndex}, {"index": "i", "position": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.getGridBitWithLoop, index, position, useGlobalIndex)
