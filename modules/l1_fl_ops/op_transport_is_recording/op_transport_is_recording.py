import transport


def op_transport_is_recording() -> dict:
    """Run transport.isRecording inside FL Studio and return the outcome as a result dict."""
    return _run(transport.isRecording)
