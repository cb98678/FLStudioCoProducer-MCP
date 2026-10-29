import transport


def op_transport_get_loop_mode() -> dict:
    """Run transport.getLoopMode inside FL Studio and return the outcome as a result dict."""
    return _run(transport.getLoopMode)
