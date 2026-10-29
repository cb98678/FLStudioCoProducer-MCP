import patterns


def op_patterns_get_active_pattern_group() -> dict:
    """Run patterns.getActivePatternGroup inside FL Studio and return the outcome as a result dict."""
    return _run(patterns.getActivePatternGroup)
