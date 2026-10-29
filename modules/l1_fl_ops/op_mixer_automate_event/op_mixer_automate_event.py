import mixer


def op_mixer_automate_event(index: int, value: int, flags: int, speed: int = 0, isIncrement: int = 0, res: float = 0) -> dict:
    """Run mixer.automateEvent inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "value": value, "flags": flags, "speed": speed, "isIncrement": isIncrement, "res": res}, {"index": "i", "value": "i", "flags": "i", "speed": "i", "isIncrement": "i", "res": "n"})
    if bad:
        return bad
    return _run(mixer.automateEvent, index, value, flags, speed, isIncrement, res)
