import device


def op_device_link_to_last_tweaked(controlIndex: int, channel: int, global_link: bool = False, eventId: int = 0) -> dict:
    """Run device.linkToLastTweaked inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"controlIndex": controlIndex, "channel": channel, "global_link": global_link, "eventId": eventId}, {"controlIndex": "i", "channel": "i", "global_link": "b", "eventId": "i"})
    if bad:
        return bad
    return _run(device.linkToLastTweaked, controlIndex, channel, global_link, eventId)
