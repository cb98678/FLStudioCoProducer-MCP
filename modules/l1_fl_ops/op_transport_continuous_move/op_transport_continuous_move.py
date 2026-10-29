import transport


def op_transport_continuous_move(speed: int, startStop: int) -> dict:
    """Run transport.continuousMove inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"speed": speed, "startStop": startStop}, {"speed": "i", "startStop": "i"})
    if bad:
        return bad
    return _run(transport.continuousMove, speed, startStop)
