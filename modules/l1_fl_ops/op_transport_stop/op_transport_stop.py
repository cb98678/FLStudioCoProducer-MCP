import transport


def op_transport_stop() -> dict:
    """Run transport.stop inside FL Studio and return the outcome as a result dict."""
    return _run(transport.stop)
