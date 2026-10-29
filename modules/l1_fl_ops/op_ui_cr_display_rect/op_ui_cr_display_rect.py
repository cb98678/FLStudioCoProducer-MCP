import ui


def op_ui_cr_display_rect(left: int, top: int, right: int, bottom: int, duration: int, flags: int = 0) -> dict:
    """Run ui.crDisplayRect inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"left": left, "top": top, "right": right, "bottom": bottom, "duration": duration, "flags": flags}, {"left": "i", "top": "i", "right": "i", "bottom": "i", "duration": "i", "flags": "i"})
    if bad:
        return bad
    return _run(ui.crDisplayRect, left, top, right, bottom, duration, flags)
