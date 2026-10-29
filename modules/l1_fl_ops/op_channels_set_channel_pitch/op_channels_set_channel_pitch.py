import channels


def op_channels_set_channel_pitch(index: int, value: float, mode: int = 0, pickupMode: int = 0, useGlobalIndex: bool = False) -> dict:
    """Run channels.setChannelPitch inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value, "mode": mode, "pickupMode": pickupMode, "useGlobalIndex": useGlobalIndex}, {"index": "i", "value": "n", "mode": "i", "pickupMode": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.setChannelPitch, index, value, mode, pickupMode, useGlobalIndex)
