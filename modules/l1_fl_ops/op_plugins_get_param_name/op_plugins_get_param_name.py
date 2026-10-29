import plugins


def op_plugins_get_param_name(paramIndex: int, index: int, slotIndex: int = -1, useGlobalIndex: bool = False) -> dict:
    """Run plugins.getParamName inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"paramIndex": paramIndex, "index": index, "slotIndex": slotIndex, "useGlobalIndex": useGlobalIndex}, {"paramIndex": "i", "index": "i", "slotIndex": "j", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(plugins.getParamName, paramIndex, index, slotIndex, useGlobalIndex)
