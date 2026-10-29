import ui


def op_ui_toggle_browser_node(value: int = -1) -> dict:
    """Run ui.toggleBrowserNode inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"value": value}, {"value": "j"})
    if bad:
        return bad
    return _run(ui.toggleBrowserNode, value)
