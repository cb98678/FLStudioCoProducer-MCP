import general


def op_general_undo_up_down(value: int) -> dict:
    """Run general.undoUpDown inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"value": value}, {"value": "i"})
    if bad:
        return bad
    return _run(general.undoUpDown, value)
