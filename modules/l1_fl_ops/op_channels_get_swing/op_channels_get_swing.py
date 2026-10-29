import channels


def op_channels_get_swing() -> dict:
    """Run channels.getSwing inside FL Studio and return the outcome as a result dict."""
    return _run(channels.getSwing)
