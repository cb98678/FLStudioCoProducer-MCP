import plugins


def op_plugins_get_name(index: int, slotIndex: int = -1, flag: int = 0, paramIndex: int = 0, useGlobalIndex: bool = False) -> dict:
    """Run plugins.getName inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "slotIndex": slotIndex, "flag": flag, "paramIndex": paramIndex, "useGlobalIndex": useGlobalIndex}, {"index": "i", "slotIndex": "j", "flag": "i", "paramIndex": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(plugins.getName, index, slotIndex, flag, paramIndex, useGlobalIndex)
