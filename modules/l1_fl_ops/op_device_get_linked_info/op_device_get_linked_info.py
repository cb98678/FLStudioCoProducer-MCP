import device


def op_device_get_linked_info(eventID: int) -> dict:
    """Run device.getLinkedInfo inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"eventID": eventID}, {"eventID": "i"})
    if bad:
        return bad
    return _run(device.getLinkedInfo, eventID)
