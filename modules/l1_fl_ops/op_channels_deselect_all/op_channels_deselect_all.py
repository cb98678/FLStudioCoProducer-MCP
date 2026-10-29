import channels


def op_channels_deselect_all() -> dict:
    """Run channels.deselectAll inside FL Studio and return the outcome as a result dict."""
    return _run(channels.deselectAll)
