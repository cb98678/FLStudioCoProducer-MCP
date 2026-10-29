import transport


def op_transport_set_loop_mode() -> dict:
    """Run transport.setLoopMode inside FL Studio and return the outcome as a result dict."""
    return _run(transport.setLoopMode)
