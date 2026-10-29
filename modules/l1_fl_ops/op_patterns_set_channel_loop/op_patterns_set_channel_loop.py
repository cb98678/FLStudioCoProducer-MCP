import patterns


def op_patterns_set_channel_loop(channel: int, loopPoint: int) -> dict:
    """Run patterns.setChannelLoop inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"channel": channel, "loopPoint": loopPoint}, {"channel": "i", "loopPoint": "i"})
    if bad:
        return bad
    return _run(patterns.setChannelLoop, channel, loopPoint)
