import transport


def op_transport_start() -> dict:
    """Run transport.start inside FL Studio and return the outcome as a result dict."""
    return _run(transport.start)
