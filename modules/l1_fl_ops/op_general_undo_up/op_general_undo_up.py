import general


def op_general_undo_up() -> dict:
    """Run general.undoUp inside FL Studio and return the outcome as a result dict."""
    return _run(general.undoUp)
