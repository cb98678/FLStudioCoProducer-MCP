import ui


def op_ui_mi_display_dock_rect(start: int, length: int, dock_side: int, time: int) -> dict:
    """Run ui.miDisplayDockRect inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"start": start, "length": length, "dock_side": dock_side, "time": time}, {"start": "i", "length": "i", "dock_side": "i", "time": "i"})
    if bad:
        return bad
    return _run(ui.miDisplayDockRect, start, length, dock_side, time)
