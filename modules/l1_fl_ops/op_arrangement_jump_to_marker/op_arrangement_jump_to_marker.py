import arrangement


def op_arrangement_jump_to_marker(delta: int, select: bool) -> dict:
    """Run arrangement.jumpToMarker inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"delta": delta, "select": select}, {"delta": "i", "select": "b"})
    if bad:
        return bad
    return _run(arrangement.jumpToMarker, delta, select)
