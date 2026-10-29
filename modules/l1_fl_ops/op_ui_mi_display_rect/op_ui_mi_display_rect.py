import ui


def op_ui_mi_display_rect(start: int, end: int, duration: int, flags: int = 0) -> dict:
    """Run ui.miDisplayRect inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"start": start, "end": end, "duration": duration, "flags": flags}, {"start": "i", "end": "i", "duration": "i", "flags": "i"})
    if bad:
        return bad
    return _run(ui.miDisplayRect, start, end, duration, flags)
