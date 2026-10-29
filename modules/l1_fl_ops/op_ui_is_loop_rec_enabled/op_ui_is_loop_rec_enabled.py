import ui


def op_ui_is_loop_rec_enabled() -> dict:
    """Run ui.isLoopRecEnabled inside FL Studio and return the outcome as a result dict."""
    return _run(ui.isLoopRecEnabled)
