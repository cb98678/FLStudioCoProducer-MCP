import patterns


def op_patterns_get_patterns_in_group(index: int) -> dict:
    """Run patterns.getPatternsInGroup inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(patterns.getPatternsInGroup, index)
