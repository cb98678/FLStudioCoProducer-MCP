import channels


def op_channels_channel_count(globalCount: bool = False) -> dict:
    """Run channels.channelCount inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"globalCount": globalCount}, {"globalCount": "b"})
    if bad:
        return bad
    return _run(channels.channelCount, globalCount)
