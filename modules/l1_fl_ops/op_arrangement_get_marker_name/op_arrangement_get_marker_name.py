import arrangement


def op_arrangement_get_marker_name(index: int) -> dict:
    """Run arrangement.getMarkerName inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(arrangement.getMarkerName, index)
