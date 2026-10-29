import ui


def op_ui_set_time_disp_min() -> dict:
    """Run ui.setTimeDispMin inside FL Studio and return the outcome as a result dict."""
    return _run(ui.setTimeDispMin)
