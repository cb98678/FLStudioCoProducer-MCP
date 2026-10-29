import ui


def op_ui_select_window(shift: bool) -> dict:
    """Run ui.selectWindow inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"shift": shift}, {"shift": "b"})
    if bad:
        return bad
    return _run(ui.selectWindow, shift)
