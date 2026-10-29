import ui


def op_ui_get_focused_node_caption() -> dict:
    """Run ui.getFocusedNodeCaption inside FL Studio and return the outcome as a result dict."""
    return _run(ui.getFocusedNodeCaption)
