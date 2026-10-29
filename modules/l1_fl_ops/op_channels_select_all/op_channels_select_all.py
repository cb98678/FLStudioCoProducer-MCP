import channels


def op_channels_select_all() -> dict:
    """Run channels.selectAll inside FL Studio and return the outcome as a result dict."""
    return _run(channels.selectAll)
