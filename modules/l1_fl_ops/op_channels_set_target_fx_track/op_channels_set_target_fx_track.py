import channels


def op_channels_set_target_fx_track(channelIndex: int, mixerIndex: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.setTargetFxTrack inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"channelIndex": channelIndex, "mixerIndex": mixerIndex, "useGlobalIndex": useGlobalIndex}, {"channelIndex": "i", "mixerIndex": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.setTargetFxTrack, channelIndex, mixerIndex, useGlobalIndex)
