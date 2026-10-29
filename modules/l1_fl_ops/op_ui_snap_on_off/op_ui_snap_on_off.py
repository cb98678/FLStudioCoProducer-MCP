import ui


def op_ui_snap_on_off() -> dict:
    """Run ui.snapOnOff inside FL Studio and return the outcome as a result dict."""
    return _run(ui.snapOnOff)
