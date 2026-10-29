import plugins


def op_plugins_get_plugin_name(index: int, slotIndex: int = -1, userName: bool = False, useGlobalIndex: bool = False) -> dict:
    """Run plugins.getPluginName inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "slotIndex": slotIndex, "userName": userName, "useGlobalIndex": useGlobalIndex}, {"index": "i", "slotIndex": "j", "userName": "b", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(plugins.getPluginName, index, slotIndex, userName, useGlobalIndex)
