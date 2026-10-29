import ui


def op_ui_get_step_edit_mode() -> dict:
    """Run ui.getStepEditMode inside FL Studio and return the outcome as a result dict."""
    return _run(ui.getStepEditMode)
