import transport


def op_transport_fast_forward(startStop: int, flags: int = 0) -> dict:
    """Run transport.fastForward inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"startStop": startStop, "flags": flags}, {"startStop": "i", "flags": "i"})
    if bad:
        return bad
    return _run(transport.fastForward, startStop, flags)
