import general


def op_general_process_r_e_c_event(eventId: int, value: int, flags: int) -> dict:
    """Run general.processRECEvent inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"eventId": eventId, "value": value, "flags": flags}, {"eventId": "i", "value": "i", "flags": "i"})
    if bad:
        return bad
    return _run(general.processRECEvent, eventId, value, flags)
