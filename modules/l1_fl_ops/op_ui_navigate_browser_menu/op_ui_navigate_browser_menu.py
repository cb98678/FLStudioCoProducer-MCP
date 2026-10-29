import ui


def op_ui_navigate_browser_menu(direction: int, shiftHeld: bool) -> dict:
    """Run ui.navigateBrowserMenu inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"direction": direction, "shiftHeld": shiftHeld}, {"direction": "i", "shiftHeld": "b"})
    if bad:
        return bad
    return _run(ui.navigateBrowserMenu, direction, shiftHeld)
