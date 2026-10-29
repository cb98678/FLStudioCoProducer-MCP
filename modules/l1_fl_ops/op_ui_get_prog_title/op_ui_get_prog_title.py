import ui


def op_ui_get_prog_title() -> dict:
    """Run ui.getProgTitle inside FL Studio and return the outcome as a result dict."""
    return _run(ui.getProgTitle)
