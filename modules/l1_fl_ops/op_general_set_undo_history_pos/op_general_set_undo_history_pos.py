import general


def op_general_set_undo_history_pos(index: int) -> dict:
    """Run general.setUndoHistoryPos inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(general.setUndoHistoryPos, index)
