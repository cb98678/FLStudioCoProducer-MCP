import patterns


def op_patterns_set_pattern_color(index: int, color: int) -> dict:
    """Run patterns.setPatternColor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "color": color}, {"index": "i", "color": "i"})
    if bad:
        return bad
    return _run(patterns.setPatternColor, index, color)
