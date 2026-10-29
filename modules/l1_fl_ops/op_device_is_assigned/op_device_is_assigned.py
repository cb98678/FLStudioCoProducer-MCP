import device


def op_device_is_assigned() -> dict:
    """Run device.isAssigned inside FL Studio and return the outcome as a result dict."""
    return _run(device.isAssigned)
