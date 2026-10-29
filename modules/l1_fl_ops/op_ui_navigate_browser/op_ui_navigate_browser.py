import ui


def op_ui_navigate_browser(direction: int, shiftHeld: bool) -> dict:
    """Run ui.navigateBrowser inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"direction": direction, "shiftHeld": shiftHeld}, {"direction": "i", "shiftHeld": "b"})
    if bad:
        return bad
    return _run(ui.navigateBrowser, direction, shiftHeld)
