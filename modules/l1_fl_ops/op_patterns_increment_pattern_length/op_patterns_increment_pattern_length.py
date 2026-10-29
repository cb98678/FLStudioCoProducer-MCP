import patterns


def op_patterns_increment_pattern_length(index: int, delta: int) -> dict:
    """Run patterns.incrementPatternLength inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "delta": delta}, {"index": "i", "delta": "i"})
    if bad:
        return bad
    return _run(patterns.incrementPatternLength, index, delta)
