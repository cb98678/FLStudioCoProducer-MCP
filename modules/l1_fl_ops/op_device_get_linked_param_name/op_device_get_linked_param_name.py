import device


def op_device_get_linked_param_name(eventID: int) -> dict:
    """Run device.getLinkedParamName inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"eventID": eventID}, {"eventID": "i"})
    if bad:
        return bad
    return _run(device.getLinkedParamName, eventID)
