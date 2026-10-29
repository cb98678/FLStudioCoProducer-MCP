import ui


def op_ui_is_closing() -> dict:
    """Run ui.isClosing inside FL Studio and return the outcome as a result dict."""
    return _run(ui.isClosing)
