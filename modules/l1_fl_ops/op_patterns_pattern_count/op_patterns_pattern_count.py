import patterns


def op_patterns_pattern_count() -> dict:
    """Run patterns.patternCount inside FL Studio and return the outcome as a result dict."""
    return _run(patterns.patternCount)
