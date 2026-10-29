import ui


def op_ui_is_start_on_input_enabled() -> dict:
    """Run ui.isStartOnInputEnabled inside FL Studio and return the outcome as a result dict."""
    return _run(ui.isStartOnInputEnabled)
