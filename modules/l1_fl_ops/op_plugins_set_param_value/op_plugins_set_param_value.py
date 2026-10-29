import plugins


def op_plugins_set_param_value(value: float, paramIndex: int, index: int, slotIndex: int = -1, pickupMode: int = 0, useGlobalIndex: bool = False) -> dict:
    """Run plugins.setParamValue inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"value": value, "paramIndex": paramIndex, "index": index, "slotIndex": slotIndex, "pickupMode": pickupMode, "useGlobalIndex": useGlobalIndex}, {"value": "n", "paramIndex": "i", "index": "i", "slotIndex": "j", "pickupMode": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(plugins.setParamValue, value, paramIndex, index, slotIndex, pickupMode, useGlobalIndex)
