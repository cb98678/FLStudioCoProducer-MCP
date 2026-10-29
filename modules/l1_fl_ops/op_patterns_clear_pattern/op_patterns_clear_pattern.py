import patterns


def op_patterns_clear_pattern(index: int) -> dict:
    """Run patterns.clearPattern inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(patterns.clearPattern, index)
