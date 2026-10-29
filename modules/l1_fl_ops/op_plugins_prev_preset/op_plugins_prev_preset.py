import plugins


def op_plugins_prev_preset(index: int, slotIndex: int = -1, useGlobalIndex: bool = False) -> dict:
    """Run plugins.prevPreset inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "slotIndex": slotIndex, "useGlobalIndex": useGlobalIndex}, {"index": "i", "slotIndex": "j", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(plugins.prevPreset, index, slotIndex, useGlobalIndex)
