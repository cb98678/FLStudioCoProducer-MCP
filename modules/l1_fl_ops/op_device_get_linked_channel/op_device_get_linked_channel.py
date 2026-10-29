import device


def op_device_get_linked_channel(eventId: int) -> dict:
    """Run device.getLinkedChannel inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"eventId": eventId}, {"eventId": "i"})
    if bad:
        return bad
    return _run(device.getLinkedChannel, eventId)
