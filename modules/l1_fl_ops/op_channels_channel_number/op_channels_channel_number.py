import channels


def op_channels_channel_number(canBeNone: bool = False, offset: int = 0) -> dict:
    """Run channels.channelNumber inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"canBeNone": canBeNone, "offset": offset}, {"canBeNone": "b", "offset": "i"})
    if bad:
        return bad
    return _run(channels.channelNumber, canBeNone, offset)
