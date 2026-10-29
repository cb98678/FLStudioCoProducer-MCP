import patterns


def op_patterns_get_pattern_group_count() -> dict:
    """Run patterns.getPatternGroupCount inside FL Studio and return the outcome as a result dict."""
    return _run(patterns.getPatternGroupCount)
