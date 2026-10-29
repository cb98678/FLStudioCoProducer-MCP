import channels


def op_channels_inc_event_value(eventId: int, step: int, res: float = 0) -> dict:
    """Run channels.incEventValue inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"eventId": eventId, "step": step, "res": res}, {"eventId": "i", "step": "i", "res": "n"})
    if bad:
        return bad
    return _run(channels.incEventValue, eventId, step, res)
