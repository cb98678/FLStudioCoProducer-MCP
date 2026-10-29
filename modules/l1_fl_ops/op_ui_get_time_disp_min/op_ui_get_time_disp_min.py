import ui


def op_ui_get_time_disp_min() -> dict:
    """Run ui.getTimeDispMin inside FL Studio and return the outcome as a result dict."""
    return _run(ui.getTimeDispMin)
