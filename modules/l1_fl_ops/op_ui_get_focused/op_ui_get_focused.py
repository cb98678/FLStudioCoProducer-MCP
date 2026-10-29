import ui


def op_ui_get_focused(index: int) -> dict:
    """Run ui.getFocused inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(ui.getFocused, index)
