import ui


def op_ui_is_browser_auto_hide() -> dict:
    """Run ui.isBrowserAutoHide inside FL Studio and return the outcome as a result dict."""
    return _run(ui.isBrowserAutoHide)
