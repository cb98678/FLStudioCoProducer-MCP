import ui


def op_ui_select_browser_menu_item() -> dict:
    """Run ui.selectBrowserMenuItem inside FL Studio and return the outcome as a result dict."""
    return _run(ui.selectBrowserMenuItem)
