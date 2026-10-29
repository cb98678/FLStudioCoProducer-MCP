import ui


def op_ui_preview_browser_menu_item() -> dict:
    """Run ui.previewBrowserMenuItem inside FL Studio and return the outcome as a result dict."""
    return _run(ui.previewBrowserMenuItem)
