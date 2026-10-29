import ui


def op_ui_get_hint_msg() -> dict:
    """Run ui.getHintMsg inside FL Studio and return the outcome as a result dict."""
    return _run(ui.getHintMsg)
