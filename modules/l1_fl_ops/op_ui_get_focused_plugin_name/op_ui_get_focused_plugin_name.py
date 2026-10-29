import ui


def op_ui_get_focused_plugin_name() -> dict:
    """Run ui.getFocusedPluginName inside FL Studio and return the outcome as a result dict."""
    return _run(ui.getFocusedPluginName)
