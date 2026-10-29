import channels


def op_channels_update_graph_editor() -> dict:
    """Run channels.updateGraphEditor inside FL Studio and return the outcome as a result dict."""
    return _run(channels.updateGraphEditor)
