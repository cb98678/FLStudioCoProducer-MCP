import arrangement


def op_arrangement_live_selection(time: int, stop: bool) -> dict:
    """Run arrangement.liveSelection inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"time": time, "stop": stop}, {"time": "i", "stop": "b"})
    if bad:
        return bad
    return _run(arrangement.liveSelection, time, stop)
