import general


def op_general_get_undo_history_pos() -> dict:
    """Run general.getUndoHistoryPos inside FL Studio and return the outcome as a result dict."""
    return _run(general.getUndoHistoryPos)
