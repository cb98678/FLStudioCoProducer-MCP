import patterns


def op_patterns_get_block_set_status(left: int, top: int, right: int, bottom: int) -> dict:
    """Run patterns.getBlockSetStatus inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"left": left, "top": top, "right": right, "bottom": bottom}, {"left": "i", "top": "i", "right": "i", "bottom": "i"})
    if bad:
        return bad
    return _run(patterns.getBlockSetStatus, left, top, right, bottom)
