import arrangement


def op_arrangement_current_time(snap: int) -> dict:
    """Run arrangement.currentTime inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"snap": snap}, {"snap": "i"})
    if bad:
        return bad
    return _run(arrangement.currentTime, snap)
