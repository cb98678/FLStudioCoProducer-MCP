import general


def op_general_get_undo_history_last() -> dict:
    """Run general.getUndoHistoryLast inside FL Studio and return the outcome as a result dict."""
    return _run(general.getUndoHistoryLast)
