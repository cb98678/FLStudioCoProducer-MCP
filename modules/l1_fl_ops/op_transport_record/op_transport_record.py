import transport


def op_transport_record() -> dict:
    """Run transport.record inside FL Studio and return the outcome as a result dict."""
    return _run(transport.record)
