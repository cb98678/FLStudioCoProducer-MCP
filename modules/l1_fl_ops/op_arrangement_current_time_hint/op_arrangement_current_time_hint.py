import arrangement


def op_arrangement_current_time_hint(mode: int, time: int, setRecPPB: int = 0, isLength: int = 0) -> dict:
    """Run arrangement.currentTimeHint inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"mode": mode, "time": time, "setRecPPB": setRecPPB, "isLength": isLength}, {"mode": "i", "time": "i", "setRecPPB": "i", "isLength": "i"})
    if bad:
        return bad
    return _run(arrangement.currentTimeHint, mode, time, setRecPPB, isLength)
