import patterns


def op_patterns_set_pattern_name(index: int, name: str) -> dict:
    """Run patterns.setPatternName inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "name": name}, {"index": "i", "name": "s"})
    if bad:
        return bad
    return _run(patterns.setPatternName, index, name)
