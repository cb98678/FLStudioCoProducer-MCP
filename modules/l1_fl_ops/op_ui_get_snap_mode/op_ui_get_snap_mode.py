import ui


def op_ui_get_snap_mode() -> dict:
    """Run ui.getSnapMode inside FL Studio and return the outcome as a result dict."""
    return _run(ui.getSnapMode)
