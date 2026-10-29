import transport


def op_transport_is_playing() -> dict:
    """Run transport.isPlaying inside FL Studio and return the outcome as a result dict."""
    return _run(transport.isPlaying)
