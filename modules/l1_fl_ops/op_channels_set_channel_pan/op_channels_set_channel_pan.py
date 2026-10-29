import channels


def op_channels_set_channel_pan(index: int, pan: float, pickupMode: int = 0, useGlobalIndex: bool = False) -> dict:
    """Run channels.setChannelPan inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "pan": pan, "pickupMode": pickupMode, "useGlobalIndex": useGlobalIndex}, {"index": "i", "pan": "n", "pickupMode": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.setChannelPan, index, pan, pickupMode, useGlobalIndex)
