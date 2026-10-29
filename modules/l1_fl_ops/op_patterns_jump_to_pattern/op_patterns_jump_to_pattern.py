import patterns


def op_patterns_jump_to_pattern(index: int) -> dict:
    """Run patterns.jumpToPattern inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(patterns.jumpToPattern, index)
