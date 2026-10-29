import ui


def op_ui_snap_mode(value: int) -> dict:
    """Run ui.snapMode inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"value": value}, {"value": "i"})
    if bad:
        return bad
    return _run(ui.snapMode, value)
