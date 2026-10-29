import device


def op_device_is_midi_out_assigned() -> dict:
    """Run device.isMidiOutAssigned inside FL Studio and return the outcome as a result dict."""
    return _run(device.isMidiOutAssigned)
