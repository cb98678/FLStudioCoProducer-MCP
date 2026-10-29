import channels


def op_channels_get_channel_pitch(index: int, mode: int = 0, useGlobalIndex: bool = False) -> dict:
    """Run channels.getChannelPitch inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "mode": mode, "useGlobalIndex": useGlobalIndex}, {"index": "i", "mode": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.getChannelPitch, index, mode, useGlobalIndex)
