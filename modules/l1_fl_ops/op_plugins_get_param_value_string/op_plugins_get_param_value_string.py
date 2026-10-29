import plugins


def op_plugins_get_param_value_string(paramIndex: int, index: int, slotIndex: int = -1, useGlobalIndex: bool = False) -> dict:
    """Run plugins.getParamValueString inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"paramIndex": paramIndex, "index": index, "slotIndex": slotIndex, "useGlobalIndex": useGlobalIndex}, {"paramIndex": "i", "index": "i", "slotIndex": "j", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(plugins.getParamValueString, paramIndex, index, slotIndex, useGlobalIndex)
