import general


def op_general_undo_down() -> dict:
    """Run general.undoDown inside FL Studio and return the outcome as a result dict."""
    return _run(general.undoDown)
