import device


def op_device_find_event_i_d(controlId: int, flags: int = 0) -> dict:
    """Run device.findEventID inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"controlId": controlId, "flags": flags}, {"controlId": "i", "flags": "i"})
    if bad:
        return bad
    return _run(device.findEventID, controlId, flags)
