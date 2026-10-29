import patterns


def op_patterns_is_pattern_selected(index: int) -> dict:
    """Run patterns.isPatternSelected inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(patterns.isPatternSelected, index)
