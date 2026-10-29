import ui


def op_ui_get_focused_form_i_d() -> dict:
    """Run ui.getFocusedFormID inside FL Studio and return the outcome as a result dict."""
    return _run(ui.getFocusedFormID)
