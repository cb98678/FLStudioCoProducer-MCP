import ui


def op_ui_hide_window(index: int) -> dict:
    """Run ui.hideWindow inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(ui.hideWindow, index)
