import patterns


def op_patterns_get_channel_loop_style(pattern: int, channel: int) -> dict:
    """Run patterns.getChannelLoopStyle inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"pattern": pattern, "channel": channel}, {"pattern": "i", "channel": "i"})
    if bad:
        return bad
    return _run(patterns.getChannelLoopStyle, pattern, channel)
