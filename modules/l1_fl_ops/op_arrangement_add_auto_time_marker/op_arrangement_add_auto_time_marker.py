import arrangement


def op_arrangement_add_auto_time_marker(time: int, name: str) -> dict:
    """Run arrangement.addAutoTimeMarker inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"time": time, "name": name}, {"time": "i", "name": "s"})
    if bad:
        return bad
    return _run(arrangement.addAutoTimeMarker, time, name)
