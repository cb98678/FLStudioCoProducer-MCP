import mixer


def op_mixer_get_event_i_d_value_string(index: int, value: int) -> dict:
    """Run mixer.getEventIDValueString inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value}, {"index": "i", "value": "i"})
    if bad:
        return bad
    return _run(mixer.getEventIDValueString, index, value)
