import transport


def op_transport_rewind(startStop: int, flags: int = 0) -> dict:
    """Run transport.rewind inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"startStop": startStop, "flags": flags}, {"startStop": "i", "flags": "i"})
    if bad:
        return bad
    return _run(transport.rewind, startStop, flags)
