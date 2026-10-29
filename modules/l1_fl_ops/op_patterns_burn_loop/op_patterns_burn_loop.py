import patterns


def op_patterns_burn_loop(index: int, storeUndo: int = 1, updateUi: int = 1) -> dict:
    """Run patterns.burnLoop inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "storeUndo": storeUndo, "updateUi": updateUi}, {"index": "i", "storeUndo": "i", "updateUi": "i"})
    if bad:
        return bad
    return _run(patterns.burnLoop, index, storeUndo, updateUi)
