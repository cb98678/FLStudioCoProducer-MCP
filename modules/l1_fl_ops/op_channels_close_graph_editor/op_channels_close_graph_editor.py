import channels


def op_channels_close_graph_editor(index: int) -> dict:
    """Run channels.closeGraphEditor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(channels.closeGraphEditor, index)
