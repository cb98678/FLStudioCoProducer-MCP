import transport


def op_transport_marker_jump_jog(value: int, flags: int = 0) -> dict:
    """Run transport.markerJumpJog inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"value": value, "flags": flags}, {"value": "i", "flags": "i"})
    if bad:
        return bad
    return _run(transport.markerJumpJog, value, flags)
