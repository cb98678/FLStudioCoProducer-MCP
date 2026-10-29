import ui


def op_ui_set_focused(index: int) -> dict:
    """Run ui.setFocused inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(ui.setFocused, index)
