import channels


def op_channels_is_grid_bit_assigned(index: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.isGridBitAssigned inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "useGlobalIndex": useGlobalIndex}, {"index": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.isGridBitAssigned, index, useGlobalIndex)
