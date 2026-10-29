import channels


def op_channels_show_graph_editor(temporary: bool, param: int, step: int, index: int, useGlobalIndex: bool = True) -> dict:
    """Run channels.showGraphEditor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"temporary": temporary, "param": param, "step": step, "index": index, "useGlobalIndex": useGlobalIndex}, {"temporary": "b", "param": "i", "step": "i", "index": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.showGraphEditor, temporary, param, step, index, useGlobalIndex)
