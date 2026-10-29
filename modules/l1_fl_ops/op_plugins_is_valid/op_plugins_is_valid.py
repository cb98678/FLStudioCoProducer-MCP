import plugins


def op_plugins_is_valid(index: int, slotIndex: int = -1, useGlobalIndex: bool = False) -> dict:
    """Run plugins.isValid inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "slotIndex": slotIndex, "useGlobalIndex": useGlobalIndex}, {"index": "i", "slotIndex": "j", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(plugins.isValid, index, slotIndex, useGlobalIndex)
