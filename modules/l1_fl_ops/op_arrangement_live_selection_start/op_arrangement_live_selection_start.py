import arrangement


def op_arrangement_live_selection_start() -> dict:
    """Run arrangement.liveSelectionStart inside FL Studio and return the outcome as a result dict."""
    return _run(arrangement.liveSelectionStart)
