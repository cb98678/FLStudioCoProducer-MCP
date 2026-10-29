import patterns


def op_patterns_select_pattern(index: int, value: int = -1, preview: bool = False) -> dict:
    """Run patterns.selectPattern inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value, "preview": preview}, {"index": "i", "value": "j", "preview": "b"})
    if bad:
        return bad
    return _run(patterns.selectPattern, index, value, preview)
