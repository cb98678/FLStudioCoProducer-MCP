import patterns


def op_patterns_get_pattern_name(index: int) -> dict:
    """Run patterns.getPatternName inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(patterns.getPatternName, index)
