import arrangement


def op_arrangement_selection_end() -> dict:
    """Run arrangement.selectionEnd inside FL Studio and return the outcome as a result dict."""
    return _run(arrangement.selectionEnd)
