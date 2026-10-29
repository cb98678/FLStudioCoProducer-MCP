import general


def op_general_get_undo_history_count() -> dict:
    """Run general.getUndoHistoryCount inside FL Studio and return the outcome as a result dict."""
    return _run(general.getUndoHistoryCount)
