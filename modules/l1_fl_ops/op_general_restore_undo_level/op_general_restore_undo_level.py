import general


def op_general_restore_undo_level(level: int) -> dict:
    """Run general.restoreUndoLevel inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"level": level}, {"level": "i"})
    if bad:
        return bad
    return _run(general.restoreUndoLevel, level)
