import patterns


def op_patterns_select_all() -> dict:
    """Run patterns.selectAll inside FL Studio and return the outcome as a result dict."""
    return _run(patterns.selectAll)
