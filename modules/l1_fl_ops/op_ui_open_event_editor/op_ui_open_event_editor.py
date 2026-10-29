import ui


def op_ui_open_event_editor(eventId: int, mode: int, newWindow: bool = False) -> dict:
    """Run ui.openEventEditor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"eventId": eventId, "mode": mode, "newWindow": newWindow}, {"eventId": "i", "mode": "i", "newWindow": "b"})
    if bad:
        return bad
    return _run(ui.openEventEditor, eventId, mode, newWindow)
