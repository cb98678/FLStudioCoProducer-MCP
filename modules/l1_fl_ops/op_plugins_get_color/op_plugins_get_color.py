import plugins


def op_plugins_get_color(index: int, slotIndex: int = -1, flag: int = 0, useGlobalIndex: bool = False) -> dict:
    """Run plugins.getColor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "slotIndex": slotIndex, "flag": flag, "useGlobalIndex": useGlobalIndex}, {"index": "i", "slotIndex": "j", "flag": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(plugins.getColor, index, slotIndex, flag, useGlobalIndex)
