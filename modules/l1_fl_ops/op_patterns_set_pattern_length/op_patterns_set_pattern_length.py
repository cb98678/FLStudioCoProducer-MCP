import patterns


def op_patterns_set_pattern_length(index: int, length: int) -> dict:
    """Run patterns.setPatternLength inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "length": length}, {"index": "i", "length": "i"})
    if bad:
        return bad
    return _run(patterns.setPatternLength, index, length)
