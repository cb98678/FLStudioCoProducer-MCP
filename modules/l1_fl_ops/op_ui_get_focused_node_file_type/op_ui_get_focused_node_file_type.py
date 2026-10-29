import ui


def op_ui_get_focused_node_file_type() -> dict:
    """Run ui.getFocusedNodeFileType inside FL Studio and return the outcome as a result dict."""
    return _run(ui.getFocusedNodeFileType)
