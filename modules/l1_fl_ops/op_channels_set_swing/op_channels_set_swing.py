import channels


def op_channels_set_swing(value: float) -> dict:
    """Run channels.setSwing inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"value": value}, {"value": "n"})
    if bad:
        return bad
    return _run(channels.setSwing, value)
