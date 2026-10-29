import ui


def op_ui_set_browser_auto_hide(value: bool) -> dict:
    """Run ui.setBrowserAutoHide inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"value": value}, {"value": "b"})
    if bad:
        return bad
    return _run(ui.setBrowserAutoHide, value)
