import channels


def op_channels_is_high_lighted() -> dict:
    """Run channels.isHighLighted inside FL Studio and return the outcome as a result dict."""
    return _run(channels.isHighLighted)
