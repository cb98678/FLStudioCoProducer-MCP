import ui


def op_ui_is_precount_enabled() -> dict:
    """Run ui.isPrecountEnabled inside FL Studio and return the outcome as a result dict."""
    return _run(ui.isPrecountEnabled)
