import ui


def op_ui_scroll_window(index: int, value: int, directionFlag: int = 0) -> dict:
    """Run ui.scrollWindow inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value, "directionFlag": directionFlag}, {"index": "i", "value": "i", "directionFlag": "i"})
    if bad:
        return bad
    return _run(ui.scrollWindow, index, value, directionFlag)
