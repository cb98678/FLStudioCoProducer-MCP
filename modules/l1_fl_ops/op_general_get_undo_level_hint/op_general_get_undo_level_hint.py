import general


def op_general_get_undo_level_hint() -> dict:
    """Run general.getUndoLevelHint inside FL Studio and return the outcome as a result dict."""
    return _run(general.getUndoLevelHint)
