import arrangement


def op_arrangement_selection_start() -> dict:
    """Run arrangement.selectionStart inside FL Studio and return the outcome as a result dict."""
    return _run(arrangement.selectionStart)
