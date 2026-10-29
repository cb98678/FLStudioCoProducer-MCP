import ui


def op_ui_hor_zoom(value: int) -> dict:
    """Run ui.horZoom inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"value": value}, {"value": "i"})
    if bad:
        return bad
    return _run(ui.horZoom, value)
