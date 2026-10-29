import plugins


def op_plugins_get_pad_info(chanIndex: int, slotIndex: int = -1, paramOption: int = 0, paramIndex: int = -1, useGlobalIndex: bool = False) -> dict:
    """Run plugins.getPadInfo inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"chanIndex": chanIndex, "slotIndex": slotIndex, "paramOption": paramOption, "paramIndex": paramIndex, "useGlobalIndex": useGlobalIndex}, {"chanIndex": "i", "slotIndex": "j", "paramOption": "i", "paramIndex": "j", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(plugins.getPadInfo, chanIndex, slotIndex, paramOption, paramIndex, useGlobalIndex)
