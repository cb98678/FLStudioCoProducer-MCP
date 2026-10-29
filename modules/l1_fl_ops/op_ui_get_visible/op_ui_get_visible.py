import ui


def op_ui_get_visible(index: int) -> dict:
    """Run ui.getVisible inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(ui.getVisible, index)
