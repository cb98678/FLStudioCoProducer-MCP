import channels


def op_channels_get_channel_index(index: int) -> dict:
    """Run channels.getChannelIndex inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(channels.getChannelIndex, index)
