import ui


def op_ui_get_hint_value(value: int, max: int) -> dict:
    """Run ui.getHintValue inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"value": value, "max": max}, {"value": "i", "max": "i"})
    if bad:
        return bad
    return _run(ui.getHintValue, value, max)
