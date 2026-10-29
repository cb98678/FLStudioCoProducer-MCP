import patterns


def op_patterns_find_first_next_empty_pat(flags: int, x: int = -1, y: int = -1) -> dict:
    """Run patterns.findFirstNextEmptyPat inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"flags": flags, "x": x, "y": y}, {"flags": "i", "x": "j", "y": "j"})
    if bad:
        return bad
    return _run(patterns.findFirstNextEmptyPat, flags, x, y)
