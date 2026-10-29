import ui


def op_ui_show_window(index: int) -> dict:
    """Run ui.showWindow inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(ui.showWindow, index)
