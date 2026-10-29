import ui


def op_ui_get_focused_form_caption() -> dict:
    """Run ui.getFocusedFormCaption inside FL Studio and return the outcome as a result dict."""
    return _run(ui.getFocusedFormCaption)
