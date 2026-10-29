import general


def op_general_set_undo_history_count(value: int) -> dict:
    """Run general.setUndoHistoryCount inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"value": value}, {"value": "i"})
    if bad:
        return bad
    return _run(general.setUndoHistoryCount, value)
