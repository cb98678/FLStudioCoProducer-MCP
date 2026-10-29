import channels


def op_channels_set_channel_volume(index: int, volume: float, pickupMode: int = 0, useGlobalIndex: bool = False) -> dict:
    """Run channels.setChannelVolume inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "volume": volume, "pickupMode": pickupMode, "useGlobalIndex": useGlobalIndex}, {"index": "i", "volume": "n", "pickupMode": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.setChannelVolume, index, volume, pickupMode, useGlobalIndex)
