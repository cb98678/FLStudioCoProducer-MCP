import general


def op_general_restore_undo() -> dict:
    """Run general.restoreUndo inside FL Studio and return the outcome as a result dict."""
    return _run(general.restoreUndo)
