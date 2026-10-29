import channels


def op_channels_process_r_e_c_event(eventId: int, value: int, flags: int) -> dict:
    """Run channels.processRECEvent inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"eventId": eventId, "value": value, "flags": flags}, {"eventId": "i", "value": "i", "flags": "i"})
    if bad:
        return bad
    return _run(channels.processRECEvent, eventId, value, flags)
