import transport


def op_transport_continuous_move_pos(speed: int, startStop: int) -> dict:
    """Run transport.continuousMovePos inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"speed": speed, "startStop": startStop}, {"speed": "i", "startStop": "i"})
    if bad:
        return bad
    return _run(transport.continuousMovePos, speed, startStop)
