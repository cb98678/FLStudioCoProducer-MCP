import ui


def op_ui_navigate_browser_tabs(direction: int) -> dict:
    """Run ui.navigateBrowserTabs inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"direction": direction}, {"direction": "i"})
    if bad:
        return bad
    return _run(ui.navigateBrowserTabs, direction)
