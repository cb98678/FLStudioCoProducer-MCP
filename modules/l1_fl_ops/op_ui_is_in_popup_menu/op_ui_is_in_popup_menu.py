import ui


def op_ui_is_in_popup_menu() -> dict:
    """Run ui.isInPopupMenu inside FL Studio and return the outcome as a result dict."""
    return _run(ui.isInPopupMenu)
