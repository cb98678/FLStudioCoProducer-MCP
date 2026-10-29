import patterns


def op_patterns_deselect_all() -> dict:
    """Run patterns.deselectAll inside FL Studio and return the outcome as a result dict."""
    return _run(patterns.deselectAll)
