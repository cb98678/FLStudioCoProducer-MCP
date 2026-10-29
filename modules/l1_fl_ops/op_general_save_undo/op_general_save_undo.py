import general


def op_general_save_undo(undoName: str, flags: int, update: bool = True) -> dict:
    """Run general.saveUndo inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"undoName": undoName, "flags": flags, "update": update}, {"undoName": "s", "flags": "i", "update": "b"})
    if bad:
        return bad
    return _run(general.saveUndo, undoName, flags, update)
