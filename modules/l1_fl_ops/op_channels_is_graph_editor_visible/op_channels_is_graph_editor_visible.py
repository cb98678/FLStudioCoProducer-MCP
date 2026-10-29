import channels


def op_channels_is_graph_editor_visible() -> dict:
    """Run channels.isGraphEditorVisible inside FL Studio and return the outcome as a result dict."""
    return _run(channels.isGraphEditorVisible)
